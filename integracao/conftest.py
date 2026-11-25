"""Testes de integração: frontend Flask + backend FastAPI reais, no mesmo processo.

As chamadas HTTP que o frontend faz com `requests` são desviadas para o
TestClient do backend por um adaptador, sem abrir portas de rede.
"""
import io
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import requests
from fastapi.testclient import TestClient
from requests.structures import CaseInsensitiveDict

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "back"), str(ROOT / "front")]

from api import create_app as create_backend  # noqa: E402
from api.config import Settings  # noqa: E402
from web import create_app as create_frontend  # noqa: E402

BACKEND_URL = "http://backend.interno"


class ASGIAdapter(requests.adapters.BaseAdapter):
    def __init__(self, test_client: TestClient):
        super().__init__()
        self.test_client = test_client

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        url = urlsplit(request.url)
        path = url.path + (f"?{url.query}" if url.query else "")
        body = request.body
        if isinstance(body, str):
            body = body.encode()
        r = self.test_client.request(request.method, path, headers=dict(request.headers), content=body)

        resp = requests.Response()
        resp.status_code = r.status_code
        resp.headers = CaseInsensitiveDict(r.headers)
        resp._content = r.content
        resp._content_consumed = True
        resp.raw = io.BytesIO(r.content)
        resp.encoding = r.encoding
        resp.url = request.url
        resp.request = request
        resp.reason = r.reason_phrase
        return resp

    def close(self):
        pass


@pytest.fixture
def backend(tmp_path):
    settings = Settings(
        secret_key="chave-de-integracao-com-mais-de-32-bytes",
        database_url=f"sqlite:///{tmp_path / 'e2e.db'}",
        storage_dir=tmp_path / "storage",
        max_upload_mb=1,
        bcrypt_rounds=4,
    )
    with TestClient(create_backend(settings)) as tc:
        yield tc


@pytest.fixture
def browser(backend):
    """Cliente de teste do Flask, como se fosse o navegador do usuário."""
    app = create_frontend(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "BACKEND_URL": BACKEND_URL, "SECRET_KEY": "teste"}
    )
    app.extensions["myfiles_http"].mount(BACKEND_URL, ASGIAdapter(backend))
    return app.test_client()
