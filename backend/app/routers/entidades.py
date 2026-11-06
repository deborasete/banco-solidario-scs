from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import exige_perfil
from ..models import EntidadeBeneficiaria, Perfil, Usuario
from ..schemas import EntidadeIn, EntidadeOut, EntidadeUpdate

router = APIRouter(prefix="/entidades", tags=["entidades (RF03)"])
coordenacao = exige_perfil(Perfil.COORDENACAO)


@router.get("", response_model=list[EntidadeOut])
def listar(
    busca: str | None = Query(None, max_length=100),
    somente_ativas: bool = True,
    db: Session = Depends(get_db),
    _: Usuario = Depends(coordenacao),
):
    consulta = select(EntidadeBeneficiaria)
    if somente_ativas:
        consulta = consulta.where(EntidadeBeneficiaria.ativa.is_(True))
    if busca:
        # Parâmetro vinculado pelo ORM: o texto nunca é concatenado no SQL (OWASP A03).
        consulta = consulta.where(EntidadeBeneficiaria.nome.ilike(f"%{busca}%"))
    return list(db.scalars(consulta.order_by(EntidadeBeneficiaria.nome)))


@router.post("", response_model=EntidadeOut, status_code=status.HTTP_201_CREATED)
def criar(dados: EntidadeIn, db: Session = Depends(get_db), _: Usuario = Depends(coordenacao)):
    entidade = EntidadeBeneficiaria(**dados.model_dump())
    db.add(entidade)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "CNPJ já cadastrado") from None
    db.refresh(entidade)
    return entidade


@router.patch("/{entidade_id}", response_model=EntidadeOut)
def atualizar(
    entidade_id: str, dados: EntidadeUpdate, db: Session = Depends(get_db), _: Usuario = Depends(coordenacao)
):
    entidade = db.get(EntidadeBeneficiaria, entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(entidade, campo, valor)
    db.commit()
    db.refresh(entidade)
    return entidade
