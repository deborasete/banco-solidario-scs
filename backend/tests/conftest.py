import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import EntidadeBeneficiaria, Perfil, TipoEntidade, Usuario
from app.security import gerar_hash

SENHA = "Senha-Forte-2026"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def entidade(db_session):
    e = EntidadeBeneficiaria(
        nome="Creche Esperança (fictícia)",
        cnpj="11222333000181",
        tipo=TipoEntidade.CRECHE,
        publico_atendido=80,
        responsavel_nome="Responsável Fictício",
        telefone="11900000000",
    )
    db_session.add(e)
    db_session.commit()
    return e


def _criar_usuario(db, perfil, entidade_id=None):
    u = Usuario(
        nome=f"Teste {perfil.value}",
        email=f"{perfil.value.lower()}-{uuid.uuid4().hex[:6]}@exemplo.org",
        senha_hash=gerar_hash(SENHA),
        perfil=perfil,
        entidade_id=entidade_id,
    )
    db.add(u)
    db.commit()
    return u


def _token(client, usuario):
    r = client.post("/auth/login", json={"email": usuario.email, "senha": SENHA})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def voluntario(db_session):
    return _criar_usuario(db_session, Perfil.VOLUNTARIO)


@pytest.fixture()
def coordenacao(db_session):
    return _criar_usuario(db_session, Perfil.COORDENACAO)


@pytest.fixture()
def h_voluntario(client, voluntario):
    return _token(client, voluntario)


@pytest.fixture()
def h_coordenacao(client, coordenacao):
    return _token(client, coordenacao)


@pytest.fixture()
def criar_usuario(db_session):
    return lambda perfil, entidade_id=None: _criar_usuario(db_session, perfil, entidade_id)


@pytest.fixture()
def token_de(client):
    return lambda usuario: _token(client, usuario)
