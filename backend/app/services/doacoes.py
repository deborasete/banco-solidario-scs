"""Serviço de doações (RF01)."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..models import Doacao, ItemDoado, StatusItem, Usuario
from ..schemas import DoacaoIn
from .regras import alerta_validade


def registrar_doacao(db: Session, dados: DoacaoIn, usuario: Usuario, hoje: date | None = None) -> tuple[Doacao, bool]:
    """Registra a doação e seus itens em uma única transação.

    É idempotente pelo id_local: se a fila offline reenviar a mesma doação,
    devolve o registro existente em vez de duplicar (retorna ja_existia=True).
    """
    existente = db.scalar(
        select(Doacao).options(selectinload(Doacao.itens)).where(Doacao.id_local == dados.id_local)
    )
    if existente:
        return existente, True

    doacao = Doacao(
        id_local=dados.id_local,
        canal=dados.canal,
        campanha_evento=dados.campanha_evento,
        observacao=dados.observacao,
        registrado_por=usuario.id,
    )
    if dados.data_recebimento:
        doacao.data_recebimento = dados.data_recebimento
    for item in dados.itens:
        doacao.itens.append(
            ItemDoado(
                categoria=item.categoria,
                descricao=item.descricao,
                unidade=item.unidade,
                quantidade_recebida=item.quantidade,
                saldo=item.quantidade,
                data_validade=item.data_validade,
                status=StatusItem.DISPONIVEL,
            )
        )
    db.add(doacao)
    db.commit()
    db.refresh(doacao)
    return doacao, False


def alertas_da_doacao(doacao: Doacao, hoje: date | None = None) -> list[str]:
    hoje = hoje or date.today()
    alertas = []
    for item in doacao.itens:
        a = alerta_validade(item.data_validade, hoje, settings.dias_alerta_validade)
        if a:
            alertas.append(f"{item.categoria.value.replace('_', ' ').title()} ({item.quantidade_recebida}): {a}")
    return alertas
