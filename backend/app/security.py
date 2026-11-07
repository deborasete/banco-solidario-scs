"""Autenticação (RNF01): hash Argon2, JWT de curta duração, revogação e bloqueio por tentativas."""
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .config import settings

_hasher = PasswordHash((Argon2Hasher(),))
ALGORITMO = "HS256"

# Senhas mais comuns rejeitadas no cadastro (lista resumida para o MVP).
SENHAS_COMUNS = {"12345678", "123456789", "senha123", "password", "qwerty123", "abcd1234", "11111111"}


def gerar_hash(senha: str) -> str:
    """Hash de mão única (Argon2id com salt aleatório). Não é criptografia reversível."""
    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return _hasher.verify(senha, senha_hash)


def senha_aceitavel(senha: str) -> bool:
    return len(senha) >= 8 and senha.lower() not in SENHAS_COMUNS


def criar_token(usuario_id: str, perfil: str, entidade_id: str | None) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario_id,
        "perfil": perfil,
        "ent": entidade_id,
        "jti": str(uuid.uuid4()),
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.jwt_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITMO)


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITMO])


class ListaRevogacao:
    """Tokens encerrados pelo botão Sair, guardados no banco (valem em qualquer instância)."""

    def revogar(self, db: Session, jti: str, exp: float) -> None:
        from .models import TokenRevogado

        agora = datetime.now(timezone.utc)
        db.execute(delete(TokenRevogado).where(TokenRevogado.expira_em < agora))
        if db.get(TokenRevogado, jti) is None:
            db.add(TokenRevogado(jti=jti, expira_em=datetime.fromtimestamp(exp, timezone.utc)))
        db.commit()

    def revogado(self, db: Session, jti: str) -> bool:
        from .models import TokenRevogado

        return db.get(TokenRevogado, jti) is not None


class LimitadorLogin:
    """Bloqueia após N falhas por chave (e-mail ou IP) dentro da janela configurada."""

    def __init__(self, maximo: int, janela_seg: int) -> None:
        self.maximo = maximo
        self.janela = janela_seg

    def bloqueado(self, db: Session, chave: str) -> bool:
        from .models import FalhaLogin

        inicio = datetime.now(timezone.utc) - timedelta(seconds=self.janela)
        db.execute(delete(FalhaLogin).where(FalhaLogin.quando < inicio))
        total = db.scalar(select(func.count()).select_from(FalhaLogin).where(FalhaLogin.chave == chave))
        return (total or 0) >= self.maximo

    def registrar_falha(self, db: Session, chave: str) -> None:
        from .models import FalhaLogin

        db.add(FalhaLogin(chave=chave[:200]))
        db.commit()

    def limpar(self, db: Session, chave: str) -> None:
        from .models import FalhaLogin

        db.execute(delete(FalhaLogin).where(FalhaLogin.chave == chave))
        db.commit()


revogacao = ListaRevogacao()
limitador = LimitadorLogin(settings.max_tentativas_login, settings.janela_bloqueio_min * 60)
