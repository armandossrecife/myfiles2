import io

import pytest

from tests.conftest import B, auth_header, media


def test_lista_de_arquivos(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/files", json=[media(1, "praia.png", size=2048)])
    page = logged.get("/arquivos").get_data(as_text=True)
    assert "praia.png" in page and "2.0 KB" in page and "25/11/2026 14:03" in page


def test_enviar_arquivo_repassa_ao_backend(logged, requests_mock):
    requests_mock.post(f"{B}/users/alice/files", status_code=201, json=media(7, "clipe.mp4", "video/mp4"))
    resp = logged.post(
        "/arquivos",
        data={"file": (io.BytesIO(b"bytes-do-video"), "clipe.mp4", "video/mp4")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 302 and resp.location.endswith("/arquivos/7")
    req = requests_mock.last_request
    assert auth_header(req) == "Bearer token-da-alice"
    assert b'name="file"; filename="clipe.mp4"' in req.body and b"bytes-do-video" in req.body


def test_enviar_sem_arquivo(logged, requests_mock):
    resp = logged.post("/arquivos", data={}, content_type="multipart/form-data")
    assert resp.status_code == 302
    assert not requests_mock.called


@pytest.mark.parametrize("status,detail", [(400, "Tipo de arquivo não permitido"), (413, "Arquivo maior que o limite")])
def test_erros_de_upload_viram_mensagem(logged, requests_mock, status, detail):
    requests_mock.post(f"{B}/users/alice/files", status_code=status, json={"detail": detail})
    requests_mock.get(f"{B}/users/alice/files", json=[])
    resp = logged.post(
        "/arquivos",
        data={"file": (io.BytesIO(b"x"), "a.exe", "application/octet-stream")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert detail in resp.get_data(as_text=True)


def test_upload_acima_do_limite_do_flask(app, logged, requests_mock):
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    resp = logged.post(
        "/arquivos",
        data={"file": (io.BytesIO(b"0" * (3 * 1024 * 1024)), "grande.mp4", "video/mp4")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 302
    assert not requests_mock.called


@pytest.mark.parametrize(
    "media_type,tag",
    [("image/png", "<img"), ("image/jpeg", "<img"), ("video/mp4", "<video"), ("audio/mpeg", "<audio")],
)
def test_visualizacao_escolhe_o_player_certo(logged, requests_mock, media_type, tag):
    requests_mock.get(f"{B}/users/alice/files/4", json=media(4, "arquivo", media_type))
    page = logged.get("/arquivos/4").get_data(as_text=True)
    assert tag in page
    assert 'src="/arquivos/4/conteudo"' in page  # navegador nunca fala direto com o backend


def test_conteudo_e_repassado_pelo_frontend(logged, requests_mock):
    requests_mock.get(
        f"{B}/users/alice/files/4/content",
        content=b"conteudo-binario",
        headers={
            "Content-Type": "audio/mpeg",
            "Content-Length": "16",
            "Content-Disposition": "inline; filename=\"musica.mp3\"",
        },
    )
    resp = logged.get("/arquivos/4/conteudo")
    assert resp.status_code == 200
    assert resp.data == b"conteudo-binario"
    assert resp.headers["Content-Type"] == "audio/mpeg"
    assert "musica.mp3" in resp.headers["Content-Disposition"]
    assert auth_header(requests_mock.last_request) == "Bearer token-da-alice"


def test_arquivo_inexistente(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/files/9", status_code=404, json={"detail": "Arquivo não encontrado"})
    assert logged.get("/arquivos/9").status_code == 404


def test_excluir_arquivo(logged, requests_mock):
    requests_mock.delete(f"{B}/users/alice/files/4", status_code=204)
    resp = logged.post("/arquivos/4/excluir")
    assert resp.status_code == 302 and resp.location.endswith("/arquivos")
    assert requests_mock.last_request.method == "DELETE"


def test_erro_inesperado_do_backend_vira_502(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/files", status_code=500, text="Internal Server Error")
    resp = logged.get("/arquivos")
    assert resp.status_code == 502
