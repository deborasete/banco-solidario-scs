"""Serviço de retiradas (RF04): baixa atômica do estoque, sem saldo negativo."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    EntidadeBeneficiaria,
    ItemDoado,
    ItemRetirada,
    Retirada,
    StatusItem,
    StatusRetirada,
    Usuario,
)
from ..schemas import RetiradaIn
from .regras import RegraNegocioError, novo_saldo


def registrar_retirada(db: Session, dados: RetiradaIn, usuario: Usuario) -> Retirada:
    entidade = db.get(EntidadeBeneficiaria, dados.entidade_id)
    if entidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada")
    if not entidade.ativa:
        raise HTTPException(status.HTTP_409_CONFLICT, "Entidade desativada não pode receber retiradas")

    ids = [i.item_id for i in dados.itens]
    if len(set(ids)) != len(ids):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cada lote deve aparecer uma única vez")

    # with_for_update trava as linhas no PostgreSQL durante a transação.
    lotes = {
        i.id: i
        for i in db.scalars(select(ItemDoado).where(ItemDoado.id.in_(ids)).with_for_update())
    }
    retirada = Retirada(
        entidade_id=entidade.id,
        status=StatusRetirada.REALIZADA,
        data_realizada=datetime.now(timezone.utc),
        registrado_por=usuario.id,
    )
    try:
        for pedido in dados.itens:
            lote = lotes.get(pedido.item_id)
            if lote is None or lote.status != StatusItem.DISPONIVEL:
                raise RegraNegocioError("Lote inexistente ou indisponível")
            lote.saldo = novo_saldo(Decimal(lote.saldo), pedido.quantidade)
            if lote.saldo == 0:
                lote.status = StatusItem.ESGOTADO
            retirada.itens.append(ItemRetirada(item_id=lote.id, quantidade=pedido.quantidade))
        db.add(retirada)
        db.commit()
    except RegraNegocioError as e:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e
    db.refresh(retirada)
    return retirada


def historico_entidade(db: Session, entidade_id: str) -> list[Retirada]:
    return list(
        db.scalars(
            select(Retirada).where(Retirada.entidade_id == entidade_id).order_by(Retirada.data_realizada.desc())
        )
    )
