"""Ponto de entrada da API na Vercel (função Python serverless).

A Vercel publica o PWA (Angular) como site estático e encaminha /api/* para esta função,
que carrega a mesma aplicação FastAPI usada localmente (pasta backend/).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))


def _url_do_banco() -> str | None:
    """Aceita a variável criada pela integração Neon/Vercel e ajusta o driver para psycopg 3."""
    url = os.environ.get("BSS_DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        return None
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


_url = _url_do_banco()
if _url:
    os.environ["BSS_DATABASE_URL"] = _url

from starlette.applications import Starlette  # noqa: E402
from starlette.routing import Mount  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app as api  # noqa: E402
from app.seed import criar_demo, garantir_coordenacao  # noqa: E402

if not _url:
    raise RuntimeError("Configure o banco: conecte o Neon (Storage) ou defina BSS_DATABASE_URL.")
if settings.jwt_secret.startswith("somente-desenvolvimento") or len(settings.jwt_secret) < 32:
    raise RuntimeError("Defina BSS_JWT_SECRET com pelo menos 32 caracteres aleatórios.")

# Sem migrações no MVP: cria as tabelas que faltarem a cada inicialização (operação idempotente).
Base.metadata.create_all(bind=engine)

# Primeiro acesso: cria a coordenação a partir de variáveis de ambiente (nada fica no código).
if os.environ.get("BSS_SEED_EMAIL") and os.environ.get("BSS_SEED_SENHA"):
    with SessionLocal() as db:
        garantir_coordenacao(db, os.environ["BSS_SEED_EMAIL"], os.environ["BSS_SEED_SENHA"])
        if os.environ.get("BSS_SEED_DEMO") == "1":
            criar_demo(db)

# /api/doacoes chega aqui; a aplicação FastAPI espera /doacoes.
app = Starlette(routes=[Mount("/api", app=api), Mount("/", app=api)])
