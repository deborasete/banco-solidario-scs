"""Serviço de estoque (RF02): saldo por categoria e lotes ordenados por validade."""
from collections import defaultdict
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Categoria, ItemDoado, StatusItem
from ..schemas import EstoqueOut, LoteEstoque, ResumoCategoria
from .regras import alerta_validade, chave_ordenacao_estoque, dias_para_vencer


def consultar_estoque(
    db: Session,
    categoria: Categoria | None = None,
    pagina: int = 1,
    por_pagina: int = 50,
    hoje: date | None = None,
) -> EstoqueOut:
    hoje = hoje or date.today()
    consulta = select(ItemDoado).where(ItemDoado.status == StatusItem.DISPONIVEL, ItemDoado.saldo > 0)
    if categoria:
        consulta = consulta.where(ItemDoado.categoria == categoria)
    itens = list(db.scalars(consulta))

    totais: dict[tuple, Decimal] = defaultdict(Decimal)
    for i in itens:
        totais[(i.categoria, i.unidade)] += Decimal(i.saldo)
    resumo = [
        ResumoCategoria(categoria=c, unidade=u, saldo_total=v)
        for (c, u), v in sorted(totais.items(), key=lambda kv: kv[0][0].value)
    ]

    itens.sort(key=lambda i: chave_ordenacao_estoque(i.data_validade, i.doacao.data_recebimento))
    inicio = (pagina - 1) * por_pagina
    lotes = [
        LoteEstoque(
            id=i.id,
            categoria=i.categoria,
            descricao=i.descricao,
            unidade=i.unidade,
            quantidade_recebida=i.quantidade_recebida,
            saldo=i.saldo,
            data_validade=i.data_validade,
            status=i.status,
            dias_para_vencer=dias_para_vencer(i.data_validade, hoje),
            alerta=alerta_validade(i.data_validade, hoje, settings.dias_alerta_validade),
            data_recebimento=i.doacao.data_recebimento,
            canal=i.doacao.canal,
        )
        for i in itens[inicio : inicio + por_pagina]
    ]
    return EstoqueOut(
        resumo=resumo, vencem_primeiro=lotes, total_lotes=len(itens), pagina=pagina, por_pagina=por_pagina
    )


def descartar_item(db: Session, item_id: str, motivo: str) -> ItemDoado:
    """Baixa que não é retirada: exige motivo e alimenta o indicador de perdas."""
    item = db.get(ItemDoado, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote não encontrado")
    if item.status != StatusItem.DISPONIVEL:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este lote não está disponível")
    item.status = StatusItem.DESCARTADO
    item.motivo_descarte = motivo
    item.saldo = Decimal("0")
    db.commit()
    db.refresh(item)
    return item
