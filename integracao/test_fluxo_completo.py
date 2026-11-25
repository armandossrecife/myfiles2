import io

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def cadastrar_e_entrar(browser, username="alice", password="segredo123"):
    resp = browser.post(
        "/register",
        data={"username": username, "email": f"{username}@ufpi.edu.br", "password": password, "repassword": password},
    )
    assert resp.status_code == 302, resp.get_data(as_text=True)
    resp = browser.post("/login", data={"username": username, "password": password})
    assert resp.status_code == 302 and resp.location.endswith("/dashboard")


def test_fluxo_completo_do_usuario(browser):
    cadastrar_e_entrar(browser)

    page = browser.get("/dashboard").get_data(as_text=True)
    assert "Olá, alice" in page

    # foto padrão e troca de foto
    assert browser.get("/perfil/foto").data.startswith(b"\x89PNG")
    browser.post("/perfil/foto", data={"image": (io.BytesIO(PNG), "eu.png")}, content_type="multipart/form-data")
    assert browser.get("/perfil/foto").data == PNG

    # anotações: criar, editar, excluir
    browser.post("/notas", data={"description": "Revisar a lista de exercícios"})
    page = browser.get("/notas").get_data(as_text=True)
    assert "Revisar a lista de exercícios" in page
    browser.post("/notas/1/editar", data={"description": "Lista revisada"})
    assert "Lista revisada" in browser.get("/notas").get_data(as_text=True)
    browser.post("/notas/1/excluir")
    assert "ainda não tem anotações" in browser.get("/notas").get_data(as_text=True)

    # arquivos: enviar, ver, baixar, excluir
    resp = browser.post(
        "/arquivos", data={"file": (io.BytesIO(b"ID3-audio"), "aula.mp3")}, content_type="multipart/form-data"
    )
    assert resp.location.endswith("/arquivos/1")
    assert "<audio" in browser.get("/arquivos/1").get_data(as_text=True)
    conteudo = browser.get("/arquivos/1/conteudo")
    assert conteudo.data == b"ID3-audio" and conteudo.headers["Content-Type"] == "audio/mpeg"
    assert 'data-testid="files-count">1<' in browser.get("/dashboard").get_data(as_text=True)
    browser.post("/arquivos/1/excluir")
    assert browser.get("/arquivos/1").status_code == 404

    # gráficos
    assert "Job A" in browser.get("/graficos/tempo").get_data(as_text=True)
    assert "Tarefa 1" in browser.get("/graficos/tarefas").get_data(as_text=True)

    # sair
    browser.post("/logout")
    assert browser.get("/dashboard").location.endswith("/login?next=/dashboard")


def test_upload_invalido_mostra_erro_do_backend(browser):
    cadastrar_e_entrar(browser)
    resp = browser.post(
        "/arquivos",
        data={"file": (io.BytesIO(b"MZ"), "virus.exe")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "Tipo de arquivo não permitido" in resp.get_data(as_text=True)


def test_upload_acima_do_limite_do_backend(browser):
    cadastrar_e_entrar(browser)
    grande = b"0" * (1024 * 1024 + 10)  # backend configurado com 1 MB
    resp = browser.post(
        "/arquivos",
        data={"file": (io.BytesIO(grande), "video.mp4")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "maior que o limite" in resp.get_data(as_text=True)


def test_cadastro_duplicado(browser):
    cadastrar_e_entrar(browser)
    browser.post("/logout")
    resp = browser.post(
        "/register",
        data={"username": "alice", "email": "outra@ufpi.edu.br", "password": "segredo123", "repassword": "segredo123"},
    )
    assert "Nome de usuário já cadastrado" in resp.get_data(as_text=True)


def test_senha_errada(browser):
    cadastrar_e_entrar(browser)
    browser.post("/logout")
    resp = browser.post("/login", data={"username": "alice", "password": "errada"})
    assert resp.status_code == 401


def test_usuarios_nao_veem_dados_um_do_outro(browser, backend):
    cadastrar_e_entrar(browser, "alice")
    browser.post("/notas", data={"description": "segredo da alice"})
    browser.post("/arquivos", data={"file": (io.BytesIO(PNG), "alice.png")}, content_type="multipart/form-data")
    browser.post("/logout")

    cadastrar_e_entrar(browser, "bob")
    assert "segredo da alice" not in browser.get("/notas").get_data(as_text=True)
    assert "alice.png" not in browser.get("/arquivos").get_data(as_text=True)
    assert browser.get("/arquivos/1").status_code == 404
    assert browser.get("/arquivos/1/conteudo").status_code == 404
    assert browser.get("/notas/1/editar").status_code == 404
