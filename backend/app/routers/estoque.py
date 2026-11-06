from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import exige_perfil
from ..models import Categoria, Perfil, Usuario
from ..schemas import DescarteIn, EstoqueOut, ItemOut
from ..services.estoque import consultar_estoque, descartar_item

router = APIRouter(prefix="/estoque", tags=["estoque (RF02)"])


@router.get("", response_model=EstoqueOut)
def ver_estoque(
    categoria: Categoria | None = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Usuario = Depends(exige_perfil(Perfil.VOLUNTARIO, Perfil.COORDENACAO)),
):
    return consultar_estoque(db, categoria, pagina, por_pagina)


@router.post("/{item_id}/descarte", response_model=ItemOut)
def descartar(
    item_id: str,
    dados: DescarteIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exige_perfil(Perfil.COORDENACAO)),
):
    return descartar_item(db, item_id, dados.motivo)
