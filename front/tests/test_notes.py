from tests.conftest import B, note


def test_lista_de_anotacoes(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/notes", json=[note(1, "Comprar <café>")])
    page = logged.get("/notas").get_data(as_text=True)
    assert "Comprar &lt;café&gt;" in page  # conteúdo escapado (sem XSS)
    assert "/notas/1/editar" in page


def test_lista_vazia(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/notes", json=[])
    assert "ainda não tem anotações" in logged.get("/notas").get_data(as_text=True)


def test_criar_anotacao(logged, requests_mock):
    requests_mock.post(f"{B}/users/alice/notes", status_code=201, json=note(5, "nova"))
    resp = logged.post("/notas", data={"description": "  nova  "})
    assert resp.status_code == 302 and resp.location.endswith("/notas")
    assert requests_mock.last_request.json() == {"description": "nova"}


def test_criar_anotacao_vazia_nao_chama_o_backend(logged, requests_mock):
    logged.post("/notas", data={"description": "   "})
    assert not requests_mock.called


def test_editar_anotacao(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/notes/3", json=note(3, "texto antigo"))
    assert "texto antigo" in logged.get("/notas/3/editar").get_data(as_text=True)

    requests_mock.put(f"{B}/users/alice/notes/3", json=note(3, "texto novo"))
    resp = logged.post("/notas/3/editar", data={"description": "texto novo"})
    assert resp.status_code == 302
    assert requests_mock.last_request.method == "PUT"
    assert requests_mock.last_request.json() == {"description": "texto novo"}


def test_excluir_anotacao(logged, requests_mock):
    requests_mock.delete(f"{B}/users/alice/notes/3", status_code=204)
    resp = logged.post("/notas/3/excluir")
    assert resp.status_code == 302
    assert requests_mock.last_request.method == "DELETE"


def test_anotacao_de_outro_usuario_mostra_404(logged, requests_mock):
    requests_mock.get(f"{B}/users/alice/notes/99", status_code=404, json={"detail": "Anotação não encontrada"})
    resp = logged.get("/notas/99/editar")
    assert resp.status_code == 404
    assert "Anotação não encontrada" in resp.get_data(as_text=True)


def test_excluir_exige_post(logged):
    assert logged.get("/notas/3/excluir").status_code == 405
