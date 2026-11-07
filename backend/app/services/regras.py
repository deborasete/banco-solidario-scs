"""Regras de negócio puras (sem banco nem HTTP), testáveis com testes unitários."""
from datetime import date, datetime
from decimal import Decimal

from ..models import PERECIVEIS, Categoria


class RegraNegocioError(Exception):
    """Violação de regra de negócio, convertida em HTTP 422/409 pela API."""


def dias_para_vencer(validade: date | None, hoje: date) -> int | None:
    if validade is None:
        return None
    return (validade - hoje).days


def alerta_validade(validade: date | None, hoje: date, limite_dias: int) -> str | None:
    """Texto do selo exibido na tela de estoque (RF02 / RNF04: texto, não só cor)."""
    dias = dias_para_vencer(validade, hoje)
    if dias is None:
        return None
    if dias < 0:
        return "Vencido"
    if dias == 0:
        return "Vence hoje"
    if dias <= limite_dias:
        return f"Vence em {dias} dia" + ("s" if dias > 1 else "")
    return None


def exige_validade(categoria: Categoria) -> bool:
    return categoria in PERECIVEIS


def novo_saldo(saldo_atual: Decimal, quantidade_retirada: Decimal) -> Decimal:
    """Uma retirada nunca pode deixar o saldo de um lote negativo (RF04)."""
    if quantidade_retirada <= 0:
        raise RegraNegocioError("A quantidade retirada deve ser maior que zero")
    if quantidade_retirada > saldo_atual:
        raise RegraNegocioError(
            f"Saldo insuficiente: o lote tem {saldo_atual} e foram pedidos {quantidade_retirada}"
        )
    return saldo_atual - quantidade_retirada


def chave_ordenacao_estoque(
    validade: date | None, recebimento: datetime | None = None
) -> tuple[int, date, datetime]:
    """Perecíveis primeiro, do que vence antes; itens sem validade vão para o fim.

    Em caso de empate na validade, sai primeiro o lote recebido antes (FIFO).
    """
    rec = recebimento.replace(tzinfo=None) if recebimento else datetime.max
    return (1, date.max, rec) if validade is None else (0, validade, rec)
