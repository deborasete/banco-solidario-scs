from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import exige_perfil, usuario_atual
from ..models import Perfil, Usuario
from ..schemas import RetiradaIn, RetiradaOut
from ..services.retiradas import historico_entidade, registrar_retirada

router = APIRouter(prefix="/retiradas", tags=["retiradas (RF04)"])


@router.post("", response_model=RetiradaOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: RetiradaIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exige_perfil(Perfil.COORDENACAO)),
):
    return registrar_retirada(db, dados, usuario)


@router.get("", response_model=list[RetiradaOut])
def listar(
    entidade_id: str | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    if usuario.perfil == Perfil.ENTIDADE:
        # O filtro vem sempre do token, nunca do parâmetro da URL (OWASP A01).
        entidade_id = usuario.entidade_id
    elif usuario.perfil != Perfil.COORDENACAO:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem permissão para esta ação")
    if not entidade_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Informe a entidade")
    return historico_entidade(db, entidade_id)
