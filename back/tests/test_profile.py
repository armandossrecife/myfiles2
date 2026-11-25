from tests.conftest import PNG_BYTES

BASE = "/users/alice/profile"


def test_perfil_inicial_usa_foto_padrao(client, alice):
    perfil = client.get(BASE, headers=alice).json()
    assert perfil["username"] == "alice"
    assert perfil["has_custom_image"] is False
    assert perfil["profile_image_url"] == "/users/alice/profile/image"

    imagem = client.get(f"{BASE}/image", headers=alice)
    assert imagem.status_code == 200
    assert imagem.headers["content-type"] == "image/png"
    assert imagem.content.startswith(b"\x89PNG")


def test_enviar_foto_de_perfil(client, alice, settings):
    resp = client.post(f"{BASE}/image", files={"image": ("eu.png", PNG_BYTES, "image/png")}, headers=alice)
    assert resp.status_code == 200
    assert resp.json()["has_custom_image"] is True
    assert client.get(f"{BASE}/image", headers=alice).content == PNG_BYTES


def test_trocar_foto_apaga_a_anterior(client, alice, settings):
    for _ in range(2):
        client.post(f"{BASE}/image", files={"image": ("eu.png", PNG_BYTES, "image/png")}, headers=alice)
    assert len(list(settings.profile_dir.iterdir())) == 1


def test_foto_com_extensao_invalida_devolve_400(client, alice):
    resp = client.post(f"{BASE}/image", files={"image": ("eu.mp4", b"x", "video/mp4")}, headers=alice)
    assert resp.status_code == 400
    assert client.get(BASE, headers=alice).json()["has_custom_image"] is False


def test_perfil_de_outro_usuario_devolve_403(client, alice, bob):
    assert client.get(BASE, headers=bob).status_code == 403
    assert client.get(f"{BASE}/image", headers=bob).status_code == 403
    resp = client.post(f"{BASE}/image", files={"image": ("x.png", PNG_BYTES, "image/png")}, headers=bob)
    assert resp.status_code == 403
