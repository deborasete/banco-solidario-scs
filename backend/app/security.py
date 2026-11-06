"""Autenticação (RNF01): hash Argon2, JWT de curta duração, revogação e bloqueio por tentativas."""
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

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
    """Tokens encerrados pelo botão Sair. Em produção, mover para o banco ou Redis."""

    def __init__(self) -> None:
        self._jtis: dict[str, float] = {}

    def revogar(self, jti: str, exp: float) -> None:
        self._jtis[jti] = exp

    def revogado(self, jti: str) -> bool:
        agora = time.time()
        self._jtis = {k: v for k, v in self._jtis.items() if v > agora}
        return jti in self._jtis


class LimitadorLogin:
    """Bloqueia após N falhas por chave (e-mail ou IP) dentro da janela configurada."""

    def __init__(self, maximo: int, janela_seg: int) -> None:
        self.maximo = maximo
        self.janela = janela_seg
        self._falhas: dict[str, deque] = defaultdict(deque)

    def _limpar(self, chave: str) -> None:
        q = self._falhas[chave]
        limite = time.time() - self.janela
        while q and q[0] < limite:
            q.popleft()

    def bloqueado(self, chave: str) -> bool:
        self._limpar(chave)
        return len(self._falhas[chave]) >= self.maximo

    def registrar_falha(self, chave: str) -> None:
        self._falhas[chave].append(time.time())

    def limpar(self, chave: str) -> None:
        self._falhas.pop(chave, None)


revogacao = ListaRevogacao()
limitador = LimitadorLogin(settings.max_tentativas_login, settings.janela_bloqueio_min * 60)
