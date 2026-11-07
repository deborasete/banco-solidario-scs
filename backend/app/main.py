"""API do Banco Solidário SCS (FastAPI)."""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .routers import auth, doacoes, entidades, estoque, retiradas

log = logging.getLogger("banco_solidario")


@asynccontextmanager
async def lifespan(_: "FastAPI"):
    # No MVP as tabelas são criadas a partir dos modelos; migrações Alembic na próxima iteração.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Banco Solidário SCS – API",
    version="1.0.0",
    description="Gestão de doações, estoque e retiradas do Banco de Alimentos (MVP acadêmico).",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def cabecalhos_seguranca(request: Request, call_next):
    resposta = await call_next(request)
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "no-referrer"
    resposta.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return resposta


@app.exception_handler(Exception)
async def erro_generico(request: Request, exc: Exception):
    # Detalhe técnico só no log; o usuário recebe mensagem genérica (OWASP A05).
    log.exception("Erro não tratado em %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Ocorreu um erro. Tente novamente."})


@app.get("/health", tags=["infra"])
def health(db: Session = Depends(get_db)):
    """Usado pelo monitoramento: confirma que a API responde e que o banco está acessível."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        log.exception("Banco indisponível no health check")
        return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponivel"})
    return {"status": "ok", "banco": "ok", "versao": app.version}


for r in (auth.router, doacoes.router, estoque.router, entidades.router, retiradas.router):
    app.include_router(r)


