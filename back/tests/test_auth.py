from datetime import timedelta

from api import seguranca
from tests.conftest import register


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_login_com_credenciais_validas_devolve_token(client):
    register(client)
    resp = client.post("/login", json={"username": "alice", "password": "segredo123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert seguranca.decode_token(body["access_token"], client.app.state.settings) == "alice"


def test_login_com_senha_errada_devolve_401(client):
    register(client)
    resp = client.post("/login", json={"username": "alice", "password": "errada"})
    assert resp.status_code == 401


def test_login_com_usuario_inexistente_devolve_401(client):
    resp = client.post("/login", json={"username": "ninguem", "password": "x"})
    assert resp.status_code == 401


def test_login_formato_oauth2_para_o_swagger(client):
    register(client)
    resp = client.post("/token", data={"username": "alice", "password": "segredo123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_rota_protegida_sem_token_devolve_401(client):
    assert client.get("/users/me").status_code == 401


def test_token_invalido_devolve_401(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer nao-e-um-jwt"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token inválido"


def test_token_expirado_devolve_401(client):
    register(client)
    token = seguranca.create_access_token("alice", client.app.state.settings, timedelta(seconds=-1))
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token expirado"


def test_token_assinado_com_outra_chave_devolve_401(client, settings):
    register(client)
    outra = settings.__class__(secret_key="outra-chave-tambem-com-32-bytes-ou-mais")
    token = seguranca.create_access_token("alice", outra)
    assert client.get("/users/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_logout(client, alice):
    assert client.post("/logout", headers=alice).status_code == 200


def test_senha_nao_e_guardada_em_texto_puro(client):
    register(client)
    with client.app.state.session_factory() as db:
        from api.banco import UserDAO

        user = UserDAO(db).get_by_username("alice")
        assert user.password_hash != "segredo123"
        assert seguranca.verify_password("segredo123", user.password_hash)
