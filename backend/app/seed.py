"""Cria o primeiro usuário da coordenação e, opcionalmente, dados fictícios de demonstração.

Uso:
    python -m app.seed --email coordenacao@exemplo.org --nome "Coordenação" --senha "<defina-uma-senha-forte>"
    python -m app.seed --demo   # adiciona entidades e doações fictícias (sem dados reais)
"""
import argparse
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import (
    Canal,
    Categoria,
    Doacao,
    EntidadeBeneficiaria,
    ItemDoado,
    Perfil,
    TipoEntidade,
    Unidade,
    Usuario,
)
from .security import gerar_hash, senha_aceitavel


def criar_demo(db) -> bool:
    """Entidades e doações fictícias. Não faz nada se já houver doações (idempotente)."""
    if db.scalar(select(Doacao.id).limit(1)) is not None:
        return False
    coord = db.scalar(select(Usuario).where(Usuario.perfil == Perfil.COORDENACAO))
    if coord is None:
        raise SystemExit("Crie antes um usuário da coordenação.")
    db.add_all([
        EntidadeBeneficiaria(nome="Creche Esperança (fictícia)", cnpj="11222333000181", tipo=TipoEntidade.CRECHE,
                             publico_atendido=80, responsavel_nome="Responsável Fictício", telefone="11900000000"),
        EntidadeBeneficiaria(nome="Lar Bem Viver (fictício)", cnpj="11444777000161",
                             tipo=TipoEntidade.ABRIGO_IDOSOS,
                             publico_atendido=35, responsavel_nome="Responsável Fictícia", telefone="11900000001"),
    ])
    hoje = date.today()
    d = Doacao(id_local=str(uuid.uuid4()), canal=Canal.DRIVE_THRU, registrado_por=coord.id)
    for cat, un, q, dias in [
        (Categoria.HORTIFRUTI, Unidade.KG, "12", 3),
        (Categoria.HORTIFRUTI, Unidade.KG, "10", 6),
        (Categoria.LATICINIOS, Unidade.UNIDADE, "4", -1),
        (Categoria.NAO_PERECIVEL, Unidade.KG, "20", None),
    ]:
        d.itens.append(ItemDoado(categoria=cat, unidade=un, quantidade_recebida=Decimal(q), saldo=Decimal(q),
                                 data_validade=hoje + timedelta(days=dias) if dias is not None else None))
    db.add(d)
    db.commit()
    return True


def garantir_coordenacao(db, email: str, senha: str, nome: str = "Coordenação") -> bool:
    """Cria a coordenação se o e-mail ainda não existir (usado também no primeiro deploy)."""
    if db.scalar(select(Usuario).where(Usuario.email == email.lower())):
        return False
    if not senha_aceitavel(senha):
        raise SystemExit("Informe uma senha forte com pelo menos 8 caracteres.")
    db.add(Usuario(nome=nome, email=email.lower(), senha_hash=gerar_hash(senha), perfil=Perfil.COORDENACAO))
    db.commit()
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--email")
    p.add_argument("--nome", default="Coordenação")
    p.add_argument("--senha")
    p.add_argument("--demo", action="store_true")
    a = p.parse_args()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if a.email:
        if not a.senha:
            raise SystemExit("Informe uma senha forte com pelo menos 8 caracteres.")
        if not garantir_coordenacao(db, a.email, a.senha, a.nome):
            raise SystemExit("E-mail já cadastrado.")
        print("Usuário da coordenação criado.")
    if a.demo and criar_demo(db):
        print("Dados fictícios de demonstração criados.")
    db.close()


if __name__ == "__main__":
    main()
