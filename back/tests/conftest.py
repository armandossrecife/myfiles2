import pytest
from fastapi.testclient import TestClient

from api import create_app
from api.config import Settings

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f"
    b"\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        secret_key="chave-de-teste-com-pelo-menos-32-bytes",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        storage_dir=tmp_path / "storage",
        max_upload_mb=1,
        bcrypt_rounds=4,  # deixa os testes rápidos
    )


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def register(client, username="alice", email=None, password="segredo123"):
    email = email or f"{username}@exemplo.com"
    return client.post("/users", json={"username": username, "email": email, "password": password})


def login(client, username="alice", password="segredo123"):
    resp = client.post("/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def alice(client):
    register(client, "alice")
    return login(client, "alice")


@pytest.fixture
def bob(client):
    register(client, "bob")
    return login(client, "bob")
