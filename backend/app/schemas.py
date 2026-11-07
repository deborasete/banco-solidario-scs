"""Esquemas Pydantic: validação na fronteira da API (RNF02)."""
import re
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from .models import (
    PERECIVEIS,
    Canal,
    Categoria,
    Perfil,
    StatusItem,
    StatusRetirada,
    TipoEntidade,
    Unidade,
)

_HTML = re.compile(r"[<>]")


def _sem_html(v: str | None) -> str | None:
    if v is not None and _HTML.search(v):
        raise ValueError("não use os caracteres < ou > neste campo")
    return v.strip() if v is not None else v


def cnpj_valido(cnpj: str) -> bool:
    d = re.sub(r"\D", "", cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False

    def dv(base: str, pesos: list[int]) -> str:
        s = sum(int(n) * p for n, p in zip(base, pesos, strict=False))
        r = s % 11
        return "0" if r < 2 else str(11 - r)

    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    p2 = [6] + p1
    return d[12] == dv(d[:12], p1) and d[13] == dv(d[:13], p2)


# ---------- Autenticação ----------
class LoginIn(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    perfil: Perfil
    nome: str


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    perfil: Perfil
    entidade_id: str | None = None

    _v = field_validator("nome")(_sem_html)

    @model_validator(mode="after")
    def entidade_obrigatoria(self):
        if self.perfil == Perfil.ENTIDADE and not self.entidade_id:
            raise ValueError("usuário de entidade precisa estar vinculado a uma entidade")
        return self


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nome: str
    email: str
    perfil: Perfil
    entidade_id: str | None


# ---------- Doações (RF01) ----------
class ItemIn(BaseModel):
    categoria: Categoria
    descricao: str | None = Field(default=None, max_length=120)
    unidade: Unidade = Unidade.KG
    quantidade: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    data_validade: date | None = None

    _v = field_validator("descricao")(_sem_html)

    @model_validator(mode="after")
    def validade_para_pereciveis(self):
        if self.categoria in PERECIVEIS and self.data_validade is None:
            raise ValueError(
                f"Informe a validade: {self.categoria.value.lower()} precisa de data"
            )
        return self


class DoacaoIn(BaseModel):
    id_local: str = Field(min_length=8, max_length=36, description="UUID gerado no celular")
    canal: Canal
    campanha_evento: str | None = Field(default=None, max_length=150)
    observacao: str | None = Field(default=None, max_length=300)
    data_recebimento: datetime | None = None
    itens: list[ItemIn] = Field(min_length=1, max_length=50)

    _v = field_validator("campanha_evento", "observacao")(_sem_html)


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    categoria: Categoria
    descricao: str | None
    unidade: Unidade
    quantidade_recebida: Decimal
    saldo: Decimal
    data_validade: date | None
    status: StatusItem


class DoacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    id_local: str
    canal: Canal
    data_recebimento: datetime
    itens: list[ItemOut]
    alertas: list[str] = []
    ja_existia: bool = False


# ---------- Estoque (RF02) ----------
class LoteEstoque(ItemOut):
    dias_para_vencer: int | None
    alerta: str | None
    # Feedback da 1ª rodada: lotes iguais precisam ser distinguíveis na tela.
    data_recebimento: datetime | None = None
    canal: Canal | None = None


class ResumoCategoria(BaseModel):
    categoria: Categoria
    unidade: Unidade
    saldo_total: Decimal


class EstoqueOut(BaseModel):
    resumo: list[ResumoCategoria]
    vencem_primeiro: list[LoteEstoque]
    total_lotes: int
    pagina: int
    por_pagina: int


class DescarteIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=200)
    _v = field_validator("motivo")(_sem_html)


# ---------- Entidades (RF03) ----------
class EntidadeIn(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    cnpj: str
    tipo: TipoEntidade
    publico_atendido: int = Field(gt=0)
    responsavel_nome: str = Field(min_length=2, max_length=120)
    telefone: str = Field(min_length=8, max_length=20)

    _v = field_validator("nome", "responsavel_nome", "telefone")(_sem_html)

    @field_validator("cnpj")
    @classmethod
    def valida_cnpj(cls, v: str) -> str:
        if not cnpj_valido(v):
            raise ValueError("CNPJ inválido")
        return re.sub(r"\D", "", v)


class EntidadeUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    publico_atendido: int | None = Field(default=None, gt=0)
    responsavel_nome: str | None = Field(default=None, min_length=2, max_length=120)
    telefone: str | None = Field(default=None, min_length=8, max_length=20)
    ativa: bool | None = None

    _v = field_validator("nome", "responsavel_nome", "telefone")(_sem_html)


class EntidadeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nome: str
    cnpj: str
    tipo: TipoEntidade
    publico_atendido: int
    responsavel_nome: str
    telefone: str
    ativa: bool


# ---------- Retiradas (RF04) ----------
class ItemRetiradaIn(BaseModel):
    item_id: str
    quantidade: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class RetiradaIn(BaseModel):
    entidade_id: str
    itens: list[ItemRetiradaIn] = Field(min_length=1, max_length=50)


class ItemRetiradaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_id: str
    quantidade: Decimal


class RetiradaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    entidade_id: str
    status: StatusRetirada
    data_realizada: datetime | None
    itens: list[ItemRetiradaOut]
