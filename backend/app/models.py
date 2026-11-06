"""Entidades do domínio (modelo definido na Experiência Prática II)."""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Perfil(str, enum.Enum):
    VOLUNTARIO = "VOLUNTARIO"
    COORDENACAO = "COORDENACAO"
    ENTIDADE = "ENTIDADE"


class Canal(str, enum.Enum):
    SEDE = "SEDE"
    DRIVE_THRU = "DRIVE_THRU"
    EVENTO = "EVENTO"
    CAMPANHA = "CAMPANHA"
    OUTRO = "OUTRO"


class Categoria(str, enum.Enum):
    NAO_PERECIVEL = "NAO_PERECIVEL"
    HORTIFRUTI = "HORTIFRUTI"
    LATICINIOS = "LATICINIOS"
    PROTEINA = "PROTEINA"
    HIGIENE_LIMPEZA = "HIGIENE_LIMPEZA"
    RACAO = "RACAO"
    OUTROS = "OUTROS"


PERECIVEIS = {Categoria.HORTIFRUTI, Categoria.LATICINIOS, Categoria.PROTEINA}


class Unidade(str, enum.Enum):
    KG = "KG"
    UNIDADE = "UNIDADE"


class StatusItem(str, enum.Enum):
    DISPONIVEL = "DISPONIVEL"
    ESGOTADO = "ESGOTADO"
    DESCARTADO = "DESCARTADO"


class StatusRetirada(str, enum.Enum):
    AGENDADA = "AGENDADA"
    REALIZADA = "REALIZADA"
    CANCELADA = "CANCELADA"


class TipoEntidade(str, enum.Enum):
    CRECHE = "CRECHE"
    ABRIGO_IDOSOS = "ABRIGO_IDOSOS"
    ASSOCIACAO = "ASSOCIACAO"
    OUTRO = "OUTRO"


class EntidadeBeneficiaria(Base):
    __tablename__ = "entidade_beneficiaria"
    __table_args__ = (CheckConstraint("publico_atendido > 0", name="ck_publico_positivo"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    nome: Mapped[str] = mapped_column(String(150))
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    tipo: Mapped[TipoEntidade] = mapped_column(Enum(TipoEntidade))
    publico_atendido: Mapped[int] = mapped_column(Integer)
    responsavel_nome: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[str] = mapped_column(String(20))
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)

    retiradas: Mapped[list["Retirada"]] = relationship(back_populates="entidade")


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    perfil: Mapped[Perfil] = mapped_column(Enum(Perfil))
    entidade_id: Mapped[str | None] = mapped_column(ForeignKey("entidade_beneficiaria.id"), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class Doacao(Base):
    __tablename__ = "doacao"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    canal: Mapped[Canal] = mapped_column(Enum(Canal))
    campanha_evento: Mapped[str | None] = mapped_column(String(150), nullable=True)
    data_recebimento: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    registrado_por: Mapped[str] = mapped_column(ForeignKey("usuario.id"))
    id_local: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    observacao: Mapped[str | None] = mapped_column(String(300), nullable=True)

    itens: Mapped[list["ItemDoado"]] = relationship(back_populates="doacao", cascade="all, delete-orphan")


class ItemDoado(Base):
    __tablename__ = "item_doado"
    __table_args__ = (
        CheckConstraint("quantidade_recebida > 0", name="ck_qtd_positiva"),
        CheckConstraint("saldo >= 0 AND saldo <= quantidade_recebida", name="ck_saldo_valido"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    doacao_id: Mapped[str] = mapped_column(ForeignKey("doacao.id"))
    categoria: Mapped[Categoria] = mapped_column(Enum(Categoria), index=True)
    descricao: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unidade: Mapped[Unidade] = mapped_column(Enum(Unidade))
    quantidade_recebida: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    saldo: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    data_validade: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[StatusItem] = mapped_column(Enum(StatusItem), default=StatusItem.DISPONIVEL)
    motivo_descarte: Mapped[str | None] = mapped_column(String(200), nullable=True)

    doacao: Mapped[Doacao] = relationship(back_populates="itens")


class Retirada(Base):
    __tablename__ = "retirada"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entidade_id: Mapped[str] = mapped_column(ForeignKey("entidade_beneficiaria.id"))
    data_agendada: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    status: Mapped[StatusRetirada] = mapped_column(Enum(StatusRetirada), default=StatusRetirada.REALIZADA)
    data_realizada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registrado_por: Mapped[str] = mapped_column(ForeignKey("usuario.id"))

    entidade: Mapped[EntidadeBeneficiaria] = relationship(back_populates="retiradas")
    itens: Mapped[list["ItemRetirada"]] = relationship(back_populates="retirada", cascade="all, delete-orphan")


class ItemRetirada(Base):
    __tablename__ = "item_retirada"
    __table_args__ = (CheckConstraint("quantidade > 0", name="ck_retirada_positiva"),)

    retirada_id: Mapped[str] = mapped_column(ForeignKey("retirada.id"), primary_key=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("item_doado.id"), primary_key=True)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    retirada: Mapped[Retirada] = relationship(back_populates="itens")
    item: Mapped[ItemDoado] = relationship()
