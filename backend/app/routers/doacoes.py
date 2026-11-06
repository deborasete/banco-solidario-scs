from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import exige_perfil
from ..models import Perfil, Usuario
from ..schemas import DoacaoIn, DoacaoOut, ItemOut
from ..services.doacoes import alertas_da_doacao, registrar_doacao

router = APIRouter(prefix="/doacoes", tags=["doações (RF01)"])


@router.post("", response_model=DoacaoOut, status_code=status.HTTP_201_CREATED)
def criar_doacao(
    dados: DoacaoIn,
    response: Response,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exige_perfil(Perfil.VOLUNTARIO, Perfil.COORDENACAO)),
):
    doacao, ja_existia = registrar_doacao(db, dados, usuario)
    if ja_existia:
        response.status_code = status.HTTP_200_OK
    return DoacaoOut(
        id=doacao.id,
        id_local=doacao.id_local,
        canal=doacao.canal,
        data_recebimento=doacao.data_recebimento,
        itens=[ItemOut.model_validate(i) for i in doacao.itens],
        alertas=alertas_da_doacao(doacao),
        ja_existia=ja_existia,
    )
