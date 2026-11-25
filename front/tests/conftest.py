"""Testes do frontend com o backend simulado por requests-mock."""
import pytest

from web import create_app

B = "http://backend.test"
NOW = "2026-11-25T14:03:00Z"
PROFILE = {
    "id": 1,
    "username": "alice",
    "email": "alice@exemplo.com",
    "profile_image_url": "/users/alice/profile/image",
    "has_custom_image": False,
}


def note(id=1, description="Comprar café"):
    return {"id": id, "description": description, "created_at": NOW, "updated_at": NOW}


def media(id=1, name="foto.png", media_type="image/png", size=2048):
    return {"id": id, "original_name": name, "media_type": media_type, "size": size, "uploaded_at": NOW}


@pytest.fixture
def app():
    return create_app(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "BACKEND_URL": B, "SECRET_KEY": "teste"}
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged(client):
    with client.session_transaction() as s:
        s["username"] = "alice"
        s["access_token"] = "token-da-alice"
    return client


def auth_header(request):
    return request.headers.get("Authorization")
