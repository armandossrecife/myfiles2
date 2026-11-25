import io

from tests.conftest import B, PROFILE, auth_header, media, note


def test_dashboard_mostra_contagens_e_recentes(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/profile", json=PROFILE)
    requests_mock.get(f"{B}/users/alice/notes", json=[note(1, "nota um"), note(2, "nota dois")])
    requests_mock.get(f"{B}/users/alice/files", json=[media(1, "praia.png")])
    resp = logged.get("/dashboard")
    page = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Olá, alice" in page
    assert 'data-testid="notes-count">2<' in page
    assert 'data-testid="files-count">1<' in page
    assert "praia.png" in page and "nota dois" in page
    assert all(auth_header(r) == "Bearer token-da-alice" for r in requests_mock.request_history)


def test_raiz_logado_vai_para_o_dashboard(logged):
    assert logged.get("/").location.endswith("/dashboard")


def test_pagina_de_perfil(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/profile", json=PROFILE)
    page = logged.get("/perfil").get_data(as_text=True)
    assert "alice@exemplo.com" in page and "Adicionar foto" in page


def test_foto_de_perfil_passa_pelo_frontend(logged, requests_mock):
    requests_mock.get(
        f"{B}/users/alice/profile/image", content=b"\x89PNG-dados", headers={"Content-Type": "image/png"}
    )
    resp = logged.get("/perfil/foto")
    assert resp.status_code == 200
    assert resp.data == b"\x89PNG-dados"
    assert resp.headers["Content-Type"] == "image/png"
    assert auth_header(requests_mock.last_request) == "Bearer token-da-alice"


def test_enviar_foto_de_perfil(logged, requests_mock):
    requests_mock.post(f"{B}/users/alice/profile/image", json={**PROFILE, "has_custom_image": True})
    resp = logged.post(
        "/perfil/foto", data={"image": (io.BytesIO(b"img"), "eu.png", "image/png")}, content_type="multipart/form-data"
    )
    assert resp.status_code == 302
    body = requests_mock.last_request.body
    assert b'name="image"; filename="eu.png"' in body and b"img" in body


def test_foto_invalida_mostra_erro_do_backend(logged, requests_mock):
    requests_mock.post(f"{B}/users/alice/profile/image", status_code=400, json={"detail": "Tipo de arquivo não permitido"})
    requests_mock.get(f"{B}/users/alice/profile", json=PROFILE)
    resp = logged.post(
        "/perfil/foto",
        data={"image": (io.BytesIO(b"x"), "eu.gif", "image/gif")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "Tipo de arquivo não permitido" in resp.get_data(as_text=True)


def test_graficos(logged, requests_mock):
    requests_mock.get(f"{B}/mytime", json=[{"Task": "Job A", "Start": "2009-01-01", "Finish": "2009-02-28"}])
    requests_mock.get(
        f"{B}/mytasks",
        json=[{"descricao": "Tarefa 1", "data_expiracao": "30/11/2026", "prioridade": 1, "concluida": False}],
    )
    tempo = logged.get("/graficos/tempo").get_data(as_text=True)
    assert "Plotly.newPlot" in tempo and "Job A" in tempo
    assert "/vendor/plotly.min.js" in tempo
    tarefas = logged.get("/graficos/tarefas").get_data(as_text=True)
    assert "Tarefa 1" in tarefas and "Pendente" in tarefas


def test_pagina_inexistente(client):
    assert client.get("/nao-existe").status_code == 404


def test_plotly_js_servido_localmente(client):
    resp = client.get("/vendor/plotly.min.js")
    assert resp.status_code == 200
    assert resp.mimetype == "application/javascript"
    assert len(resp.data) > 100_000


def test_health_nao_exige_login_nem_backend(client, requests_mock):
    resp = client.get("/health")
    assert resp.status_code == 200 and resp.get_json() == {"status": "ok"}
    assert not requests_mock.called
