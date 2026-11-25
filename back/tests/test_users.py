import pytest

from api import create_app
from tests.conftest import register


def test_cadastro_devolve_201_sem_senha(client):
    resp = register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "alice"
    assert "password" not in body and "password_hash" not in body


def test_cadastro_com_username_duplicado_devolve_409(client):
    register(client)
    resp = register(client, "alice", email="outro@exemplo.com")
    assert resp.status_code == 409


def test_cadastro_com_email_duplicado_devolve_409(client):
    register(client, "alice", email="mesmo@exemplo.com")
    resp = register(client, "carol", email="mesmo@exemplo.com")
    assert resp.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "email": "a@b.com", "password": "segredo123"},  # username curto
        {"username": "a b c", "email": "a@b.com", "password": "segredo123"},  # caracteres inválidos
        {"username": "alice", "email": "sem-arroba", "password": "segredo123"},
        {"username": "alice", "email": "a@b.com", "password": "123"},  # senha curta
        {"username": "alice", "email": "a@b.com"},  # sem senha
    ],
)
def test_cadastro_com_dados_invalidos_devolve_422(client, payload):
    assert client.post("/users", json=payload).status_code == 422


def test_users_me(client, alice):
    resp = client.get("/users/me", headers=alice)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_consultar_o_proprio_usuario(client, alice):
    resp = client.get("/users/alice", headers=alice)
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@exemplo.com"


def test_consultar_outro_usuario_devolve_403(client, alice, bob):
    assert client.get("/users/bob", headers=alice).status_code == 403


def test_dados_persistem_entre_reinicios(settings):
    """A versão antiga apagava o banco a cada start (drop_all)."""
    from fastapi.testclient import TestClient

    with TestClient(create_app(settings)) as c1:
        assert register(c1).status_code == 201
    with TestClient(create_app(settings)) as c2:
        assert c2.post("/login", json={"username": "alice", "password": "segredo123"}).status_code == 200


def test_usuario_inicial_opcional(settings):
    from fastapi.testclient import TestClient

    settings.admin_username, settings.admin_password, settings.admin_email = "armando", "armando123", "a@ufpi.edu.br"
    app = create_app(settings)
    create_app(settings)  # segunda inicialização não duplica
    with TestClient(app) as c:
        assert c.post("/login", json={"username": "armando", "password": "armando123"}).status_code == 200
