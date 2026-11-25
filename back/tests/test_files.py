from tests.conftest import PNG_BYTES

BASE = "/users/alice/files"


def upload(client, headers, name="foto.png", content=PNG_BYTES, mime="image/png", base=BASE):
    return client.post(base, files={"file": (name, content, mime)}, headers=headers)


def test_upload_lista_e_download(client, alice, settings):
    resp = upload(client, alice)
    assert resp.status_code == 201
    meta = resp.json()
    assert meta["original_name"] == "foto.png"
    assert meta["media_type"] == "image/png"
    assert meta["size"] == len(PNG_BYTES)

    # gravado no disco com nome UUID, não com o nome original
    gravados = list(settings.upload_dir.iterdir())
    assert len(gravados) == 1 and gravados[0].name != "foto.png"

    lista = client.get(BASE, headers=alice).json()
    assert [f["id"] for f in lista] == [meta["id"]]

    assert client.get(f"{BASE}/{meta['id']}", headers=alice).json()["original_name"] == "foto.png"

    conteudo = client.get(f"{BASE}/{meta['id']}/content", headers=alice)
    assert conteudo.status_code == 200
    assert conteudo.content == PNG_BYTES
    assert conteudo.headers["content-type"] == "image/png"
    assert "inline" in conteudo.headers["content-disposition"]


def test_tipos_de_midia_aceitos(client, alice):
    casos = {"a.jpg": "image/jpeg", "b.JPEG": "image/jpeg", "c.mp4": "video/mp4", "d.mp3": "audio/mpeg"}
    for nome, esperado in casos.items():
        resp = upload(client, alice, name=nome, content=b"conteudo", mime="application/octet-stream")
        assert resp.status_code == 201, nome
        assert resp.json()["media_type"] == esperado


def test_extensao_nao_permitida_devolve_400(client, alice, settings):
    assert upload(client, alice, name="script.exe", content=b"MZ").status_code == 400
    assert upload(client, alice, name="sem_extensao", content=b"x").status_code == 400
    assert list(settings.upload_dir.iterdir()) == []


def test_arquivo_vazio_devolve_400(client, alice, settings):
    assert upload(client, alice, content=b"").status_code == 400
    assert list(settings.upload_dir.iterdir()) == []


def test_arquivo_acima_do_limite_devolve_413_e_nao_fica_no_disco(client, alice, settings):
    grande = b"0" * (settings.max_upload_bytes + 1)
    assert upload(client, alice, name="video.mp4", content=grande).status_code == 413
    assert list(settings.upload_dir.iterdir()) == []
    assert client.get(BASE, headers=alice).json() == []


def test_nome_com_path_traversal_nao_escapa_da_pasta(client, alice, settings):
    resp = upload(client, alice, name="../../etc/evil.png")
    assert resp.status_code == 201
    assert len(list(settings.upload_dir.iterdir())) == 1


def test_excluir_remove_registro_e_disco(client, alice, settings):
    file_id = upload(client, alice).json()["id"]
    assert client.delete(f"{BASE}/{file_id}", headers=alice).status_code == 204
    assert list(settings.upload_dir.iterdir()) == []
    assert client.get(f"{BASE}/{file_id}", headers=alice).status_code == 404
    assert client.delete(f"{BASE}/{file_id}", headers=alice).status_code == 404


def test_usuario_ve_apenas_os_proprios_arquivos(client, alice, bob):
    file_id = upload(client, alice).json()["id"]
    upload(client, bob, name="do_bob.png", base="/users/bob/files")

    assert [f["original_name"] for f in client.get("/users/bob/files", headers=bob).json()] == ["do_bob.png"]
    assert client.get(BASE, headers=bob).status_code == 403
    assert client.get(f"/users/bob/files/{file_id}/content", headers=bob).status_code == 404
    assert client.delete(f"/users/bob/files/{file_id}", headers=bob).status_code == 404


def test_arquivos_sem_token_devolve_401(client):
    assert client.get(BASE).status_code == 401
