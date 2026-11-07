from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import exige_perfil, usuario_atual
from ..models import Perfil, Usuario
from ..schemas import LoginIn, TokenOut, UsuarioCreate, UsuarioOut
from ..security import (
    criar_token,
    gerar_hash,
    limitador,
    revogacao,
    senha_aceitavel,
    verificar_senha,
)

router = APIRouter(prefix="/auth", tags=["autenticação"])
MSG_INVALIDO = "E-mail ou senha inválidos"


@router.post("/login", response_model=TokenOut)
def login(dados: LoginIn, request: Request, db: Session = Depends(get_db)):
    chaves = [f"email:{dados.email.lower()}", f"ip:{request.client.host if request.client else '-'}"]
    if any(limitador.bloqueado(db, c) for c in chaves):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Muitas tentativas. Tente novamente em 15 minutos.")
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email.lower()))
    if usuario is None or not usuario.ativo or not verificar_senha(dados.senha, usuario.senha_hash):
        for c in chaves:
            limitador.registrar_falha(db, c)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, MSG_INVALIDO)
    for c in chaves:
        limitador.limpar(db, c)
    token = criar_token(usuario.id, usuario.perfil.value, usuario.entidade_id)
    return TokenOut(access_token=token, perfil=usuario.perfil, nome=usuario.nome)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    p = usuario._token_payload
    revogacao.revogar(db, p["jti"], float(p["exp"]))


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(usuario_atual)):
    return usuario


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exige_perfil(Perfil.COORDENACAO)),
):
    if not senha_aceitavel(dados.senha):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Senha muito fraca ou comum")
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email.lower(),
        senha_hash=gerar_hash(dados.senha),
        perfil=dados.perfil,
        entidade_id=dados.entidade_id,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado") from None
    db.refresh(usuario)
    return usuario
