"""Testes de integração: API + regras + banco (SQLite em memória)."""
import uuid
from datetime import date, timedelta

from app.models import Perfil, Usuario


def _doacao(itens, canal="DRIVE_THRU", id_local=None):
    return {"id_local": id_local or str(uuid.uuid4()), "canal": canal, "itens": itens}


def _hortifruti(qtd="12", dias=3):
    return {"categoria": "HORTIFRUTI", "unidade": "KG", "quantidade": qtd,
            "data_validade": (date.today() + timedelta(days=dias)).isoformat()}


# ---------- RNF01: autenticação ----------
def test_rota_protegida_sem_token_retorna_401(client):
    assert client.get("/estoque").status_code == 401


def test_login_invalido_mensagem_generica(client, voluntario):
    r = client.post("/auth/login", json={"email": voluntario.email, "senha": "errada"})
    assert r.status_code == 401
    assert r.json()["detail"] == "E-mail ou senha inválidos"


def test_bloqueio_apos_cinco_tentativas(client, voluntario):
    for _ in range(5):
        client.post("/auth/login", json={"email": voluntario.email, "senha": "errada"})
    r = client.post("/auth/login", json={"email": voluntario.email, "senha": "errada"})
    assert r.status_code == 429


def test_logout_revoga_token(client, h_voluntario):
    assert client.get("/auth/me", headers=h_voluntario).status_code == 200
    assert client.post("/auth/logout", headers=h_voluntario).status_code == 204
    assert client.get("/auth/me", headers=h_voluntario).status_code == 401


def test_senha_armazenada_somente_como_hash(db_session, voluntario):
    u = db_session.get(Usuario, voluntario.id)
    assert u.senha_hash.startswith("$argon2id$")


# ---------- RF01: doações ----------
def test_registrar_doacao(client, h_voluntario):
    r = client.post("/doacoes", json=_doacao([_hortifruti()]), headers=h_voluntario)
    assert r.status_code == 201, r.text
    corpo = r.json()
    assert corpo["itens"][0]["saldo"] == "12.00"
    assert any("Vence em 3 dias" in a for a in corpo["alertas"])


def test_doacao_offline_reenviada_nao_duplica(client, h_voluntario):
    payload = _doacao([_hortifruti()], id_local="fila-offline-0001")
    assert client.post("/doacoes", json=payload, headers=h_voluntario).status_code == 201
    r = client.post("/doacoes", json=payload, headers=h_voluntario)
    assert r.status_code == 200 and r.json()["ja_existia"] is True
    estoque = client.get("/estoque", headers=h_voluntario).json()
    assert estoque["total_lotes"] == 1


def test_perecivel_sem_validade_retorna_422(client, h_voluntario):
    item = {"categoria": "HORTIFRUTI", "unidade": "KG", "quantidade": "12"}
    r = client.post("/doacoes", json=_doacao([item]), headers=h_voluntario)
    assert r.status_code == 422
    assert "Informe a validade" in r.text


# ---------- RF02: estoque ----------
def test_estoque_ordenado_por_validade(client, h_voluntario):
    client.post("/doacoes", json=_doacao([_hortifruti("10", 20), _hortifruti("12", 3), _hortifruti("5", 10)]),
                headers=h_voluntario)
    e = client.get("/estoque", headers=h_voluntario).json()
    dias = [lote["dias_para_vencer"] for lote in e["vencem_primeiro"]]
    assert dias == [3, 10, 20]
    assert e["vencem_primeiro"][0]["alerta"] == "Vence em 3 dias"
    assert e["resumo"][0]["saldo_total"] == "27.00"


def test_lotes_iguais_trazem_recebimento_e_canal_em_ordem_fifo(client, h_voluntario):
    cedo = _doacao([_hortifruti("12", 3)], canal="SEDE")
    cedo["data_recebimento"] = "2026-11-07T08:00:00+00:00"
    tarde = _doacao([_hortifruti("12", 3)], canal="DRIVE_THRU")
    tarde["data_recebimento"] = "2026-11-07T15:00:00+00:00"
    for payload in (tarde, cedo):
        assert client.post("/doacoes", json=payload, headers=h_voluntario).status_code == 201
    lotes = client.get("/estoque", headers=h_voluntario).json()["vencem_primeiro"]
    assert [lote["canal"] for lote in lotes] == ["SEDE", "DRIVE_THRU"]
    assert lotes[0]["data_recebimento"].startswith("2026-11-07T08:00")


# ---------- RF03: entidades ----------
def test_cnpj_duplicado_recusado(client, h_coordenacao):
    dados = {"nome": "Associação Teste", "cnpj": "11.444.777/0001-61", "tipo": "ASSOCIACAO",
             "publico_atendido": 40, "responsavel_nome": "Fulana", "telefone": "11900000000"}
    assert client.post("/entidades", json=dados, headers=h_coordenacao).status_code == 201
    r = client.post("/entidades", json=dados, headers=h_coordenacao)
    assert r.status_code == 409 and r.json()["detail"] == "CNPJ já cadastrado"


def test_busca_com_injecao_sql_tratada_como_texto(client, h_coordenacao, entidade):
    r = client.get("/entidades", params={"busca": "' OR 1=1 --"}, headers=h_coordenacao)
    assert r.status_code == 200 and r.json() == []


# ---------- RF04: retiradas ----------
def _lote_id(client, headers, qtd="10"):
    r = client.post("/doacoes", json=_doacao([_hortifruti(qtd)]), headers=headers)
    return r.json()["itens"][0]["id"]


def test_retirada_maior_que_saldo_bloqueada(client, h_coordenacao, entidade):
    lote = _lote_id(client, h_coordenacao)
    r = client.post("/retiradas", json={"entidade_id": entidade.id, "itens": [{"item_id": lote, "quantidade": "15"}]},
                    headers=h_coordenacao)
    assert r.status_code == 409 and "Saldo insuficiente" in r.json()["detail"]


def test_retirada_reduz_saldo_e_entra_no_historico(client, h_coordenacao, entidade):
    lote = _lote_id(client, h_coordenacao)
    r = client.post("/retiradas", json={"entidade_id": entidade.id, "itens": [{"item_id": lote, "quantidade": "8"}]},
                    headers=h_coordenacao)
    assert r.status_code == 201
    e = client.get("/estoque", headers=h_coordenacao).json()
    assert e["vencem_primeiro"][0]["saldo"] == "2.00"
    hist = client.get("/retiradas", params={"entidade_id": entidade.id}, headers=h_coordenacao).json()
    assert len(hist) == 1


# ---------- OWASP A01: controle de acesso ----------
def test_voluntario_nao_registra_retirada(client, h_voluntario, entidade):
    r = client.post("/retiradas", json={"entidade_id": entidade.id, "itens": [{"item_id": "x", "quantidade": "1"}]},
                    headers=h_voluntario)
    assert r.status_code == 403


def test_entidade_so_ve_as_proprias_retiradas(client, h_coordenacao, entidade, criar_usuario, token_de):
    outra = client.post("/entidades", json={"nome": "Outra Entidade", "cnpj": "11444777000161", "tipo": "OUTRO",
                                            "publico_atendido": 10, "responsavel_nome": "Fulano",
                                            "telefone": "11900000000"}, headers=h_coordenacao).json()
    lote = _lote_id(client, h_coordenacao)
    client.post("/retiradas", json={"entidade_id": outra["id"], "itens": [{"item_id": lote, "quantidade": "1"}]},
                headers=h_coordenacao)
    usuario_a = criar_usuario(Perfil.ENTIDADE, entidade.id)
    r = client.get("/retiradas", params={"entidade_id": outra["id"]}, headers=token_de(usuario_a))
    assert r.status_code == 200 and r.json() == []


def test_cabecalhos_de_seguranca(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
