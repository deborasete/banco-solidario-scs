"""Dependências do FastAPI: usuário autenticado e autorização por perfil (OWASP A01)."""
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Perfil, Usuario
from .security import decodificar_token, revogacao

_bearer = HTTPBearer(auto_error=False)


def usuario_atual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Faça login para continuar")
    try:
        payload = decodificar_token(cred.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada") from None
    if revogacao.revogado(db, payload.get("jti", "")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão encerrada")
    usuario = db.get(Usuario, payload.get("sub"))
    if usuario is None or not usuario.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inativo")
    usuario._token_payload = payload  # usado pelo logout
    return usuario


def exige_perfil(*perfis: Perfil) -> Callable[..., Usuario]:
    def _dep(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
        if usuario.perfil not in perfis:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem permissão para esta ação")
        return usuario

    return _dep
