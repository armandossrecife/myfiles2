import requests

from tests.conftest import B, PROFILE
from web import create_app


def test_raiz_sem_login_vai_para_o_login(client):
    resp = client.get("/")
    assert resp.status_code == 302 and resp.location.endswith("/login")


def test_paginas_protegidas_exigem_login(client):
    for url in ["/dashboard", "/notas", "/arquivos", "/arquivos/1", "/perfil", "/perfil/foto", "/graficos/tempo"]:
        resp = client.get(url)
        assert resp.status_code == 302, url
        assert "/login" in resp.location


def test_tela_de_login(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "Entrar no MyFiles" in resp.get_data(as_text=True)


def test_login_com_sucesso_guarda_token_e_redireciona(client, requests_mock):
    requests_mock.post(f"{B}/login", json={"access_token": "abc", "token_type": "bearer"})
    resp = client.post("/login", data={"username": "alice", "password": "segredo123"})
    assert resp.status_code == 302 and resp.location.endswith("/dashboard")
    assert requests_mock.last_request.json() == {"username": "alice", "password": "segredo123"}
    with client.session_transaction() as s:
        assert s["username"] == "alice" and s["access_token"] == "abc"


def test_login_respeita_next_interno_e_ignora_externo(client, requests_mock):
    requests_mock.post(f"{B}/login", json={"access_token": "abc"})
    resp = client.post("/login?next=/notas", data={"username": "alice", "password": "x"})
    assert resp.location.endswith("/notas")
    resp = client.post("/login?next=https://malicioso.com", data={"username": "alice", "password": "x"})
    assert resp.location.endswith("/dashboard")


def test_login_com_senha_errada(client, requests_mock):
    requests_mock.post(f"{B}/login", status_code=401, json={"detail": "Usuário ou senha incorretos"})
    resp = client.post("/login", data={"username": "alice", "password": "errada"})
    assert resp.status_code == 401
    assert "Usuário ou senha incorretos." in resp.get_data(as_text=True)
    with client.session_transaction() as s:
        assert "access_token" not in s


def test_login_com_campos_vazios_nao_chama_o_backend(client, requests_mock):
    resp = client.post("/login", data={"username": "", "password": ""})
    assert resp.status_code == 400
    assert not requests_mock.called


def test_login_com_backend_fora_do_ar(client, requests_mock):
    requests_mock.post(f"{B}/login", exc=requests.ConnectionError)
    resp = client.post("/login", data={"username": "alice", "password": "x"})
    assert resp.status_code == 503
    assert "Não foi possível conectar ao backend" in resp.get_data(as_text=True)


def test_cadastro_com_sucesso(client, requests_mock):
    requests_mock.post(f"{B}/users", status_code=201, json={"id": 1, "username": "bob", "email": "b@x.com"})
    resp = client.post(
        "/register",
        data={"username": "bob", "email": "b@x.com", "password": "segredo123", "repassword": "segredo123"},
    )
    assert resp.status_code == 302 and resp.location.endswith("/login")
    assert requests_mock.last_request.json() == {"username": "bob", "email": "b@x.com", "password": "segredo123"}


def test_cadastro_com_senhas_diferentes(client, requests_mock):
    resp = client.post(
        "/register", data={"username": "bob", "email": "b@x.com", "password": "segredo123", "repassword": "outra123"}
    )
    assert resp.status_code == 400
    assert "As senhas não conferem." in resp.get_data(as_text=True)
    assert not requests_mock.called


def test_cadastro_duplicado_mostra_mensagem_do_backend(client, requests_mock):
    requests_mock.post(f"{B}/users", status_code=409, json={"detail": "Nome de usuário já cadastrado"})
    resp = client.post(
        "/register", data={"username": "bob", "email": "b@x.com", "password": "segredo123", "repassword": "segredo123"}
    )
    assert resp.status_code == 400
    page = resp.get_data(as_text=True)
    assert "Nome de usuário já cadastrado" in page
    assert 'value="bob"' in page  # mantém o que o usuário digitou


def test_logout_limpa_a_sessao(logged):
    resp = logged.post("/logout")
    assert resp.status_code == 302 and resp.location.endswith("/login")
    with logged.session_transaction() as s:
        assert "access_token" not in s


def test_token_expirado_no_backend_volta_para_o_login(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/profile", status_code=401, json={"detail": "Token expirado"})
    resp = logged.get("/dashboard")
    assert resp.status_code == 302 and resp.location.endswith("/login")
    with logged.session_transaction() as s:
        assert "access_token" not in s


def test_csrf_bloqueia_post_sem_token(requests_mock):
    app = create_app({"TESTING": True, "BACKEND_URL": B, "SECRET_KEY": "teste"})  # CSRF ligado
    client = app.test_client()
    resp = client.post("/login", data={"username": "alice", "password": "x"})
    assert resp.status_code == 400
    assert not requests_mock.called


def test_csrf_aceita_post_com_token(requests_mock):
    app = create_app({"TESTING": True, "BACKEND_URL": B, "SECRET_KEY": "teste"})
    client = app.test_client()
    page = client.get("/login").get_data(as_text=True)
    token = page.split('name="csrf_token" value="')[1].split('"')[0]
    requests_mock.post(f"{B}/login", json={"access_token": "abc"})
    resp = client.post("/login", data={"username": "alice", "password": "x", "csrf_token": token})
    assert resp.status_code == 302


def test_backend_url_por_variaveis_de_ambiente(monkeypatch):
    from web.config import backend_url_from_env

    monkeypatch.delenv("MYFILES_BACKEND_URL", raising=False)
    monkeypatch.setenv("BACKEND_IP", "10.0.0.5")
    monkeypatch.setenv("BACKEND_PORT", "8000")
    assert backend_url_from_env() == "http://10.0.0.5:8000"
    monkeypatch.setenv("MYFILES_BACKEND_URL", "http://api.interna:9000/")
    assert backend_url_from_env() == "http://api.interna:9000"
