"""Testes unitários das regras de negócio (sem banco e sem HTTP)."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import Categoria
from app.schemas import DoacaoIn, EntidadeIn, ItemIn, cnpj_valido
from app.security import gerar_hash, senha_aceitavel, verificar_senha
from app.services.regras import (
    RegraNegocioError,
    alerta_validade,
    chave_ordenacao_estoque,
    exige_validade,
    novo_saldo,
)

HOJE = date(2026, 10, 31)


@pytest.mark.parametrize(
    "validade,esperado",
    [
        (date(2026, 10, 30), "Vencido"),
        (date(2026, 10, 31), "Vence hoje"),
        (date(2026, 11, 1), "Vence em 1 dia"),
        (date(2026, 11, 3), "Vence em 3 dias"),
        (date(2026, 11, 7), "Vence em 7 dias"),
        (date(2026, 11, 8), None),
        (None, None),
    ],
)
def test_alerta_validade(validade, esperado):
    assert alerta_validade(validade, HOJE, 7) == esperado


def test_pereciveis_exigem_validade():
    assert exige_validade(Categoria.HORTIFRUTI)
    assert exige_validade(Categoria.LATICINIOS)
    assert not exige_validade(Categoria.NAO_PERECIVEL)


def test_novo_saldo_reduz():
    assert novo_saldo(Decimal("10"), Decimal("8")) == Decimal("2")


def test_novo_saldo_bloqueia_saldo_negativo():
    with pytest.raises(RegraNegocioError, match="Saldo insuficiente"):
        novo_saldo(Decimal("10"), Decimal("15"))


def test_ordenacao_coloca_sem_validade_no_fim():
    datas = [None, date(2026, 11, 6), date(2026, 11, 3)]
    assert sorted(datas, key=chave_ordenacao_estoque) == [date(2026, 11, 3), date(2026, 11, 6), None]


def test_empate_de_validade_sai_primeiro_o_recebido_antes():
    """Feedback da 1ª rodada: dois lotes iguais confundiam ("qual eu pego?")."""
    validade = date(2026, 11, 10)
    cedo = datetime(2026, 11, 7, 8, tzinfo=timezone.utc)
    tarde = datetime(2026, 11, 7, 15, tzinfo=timezone.utc)
    assert chave_ordenacao_estoque(validade, cedo) < chave_ordenacao_estoque(validade, tarde)
    assert chave_ordenacao_estoque(validade, None) > chave_ordenacao_estoque(validade, tarde)


def test_item_perecivel_sem_validade_e_rejeitado():
    with pytest.raises(ValidationError, match="Informe a validade"):
        ItemIn(categoria=Categoria.HORTIFRUTI, quantidade=Decimal("12"))


def test_quantidade_deve_ser_positiva():
    with pytest.raises(ValidationError):
        ItemIn(categoria=Categoria.NAO_PERECIVEL, quantidade=Decimal("0"))


def test_campo_texto_rejeita_html():
    with pytest.raises(ValidationError, match="< ou >"):
        DoacaoIn(
            id_local="abcdefgh-1234",
            canal="SEDE",
            observacao="<script>alert(1)</script>",
            itens=[{"categoria": "NAO_PERECIVEL", "quantidade": "1"}],
        )


def test_cnpj():
    assert cnpj_valido("11.222.333/0001-81")
    assert not cnpj_valido("11.222.333/0001-82")
    assert not cnpj_valido("00000000000000")
    with pytest.raises(ValidationError, match="CNPJ inválido"):
        EntidadeIn(nome="X Y", cnpj="123", tipo="CRECHE", publico_atendido=1,
                   responsavel_nome="Fulano", telefone="11900000000")


def test_hash_argon2_nao_guarda_senha_legivel():
    h = gerar_hash("Senha-Forte-2026")
    assert h.startswith("$argon2id$")
    assert "Senha-Forte-2026" not in h
    assert verificar_senha("Senha-Forte-2026", h)
    assert not verificar_senha("outra", h)


def test_senhas_fracas_rejeitadas():
    assert not senha_aceitavel("12345678")
    assert not senha_aceitavel("curta")
    assert senha_aceitavel("Senha-Forte-2026")
