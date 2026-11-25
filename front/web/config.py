"""Configuração do frontend, lida de variáveis de ambiente."""
import os

DEFAULT_SECRET = "dev-secret-frontend-troque-em-producao"


def backend_url_from_env() -> str:
    """MYFILES_BACKEND_URL tem prioridade; BACKEND_IP/BACKEND_PORT mantidos por compatibilidade."""
    url = os.getenv("MYFILES_BACKEND_URL")
    if url:
        return url.rstrip("/")
    ip, port = os.getenv("BACKEND_IP"), os.getenv("BACKEND_PORT")
    if ip and port:
        return f"http://{ip}:{port}"
    return "http://localhost:8000"


class Config:
    SECRET_KEY = os.getenv("MY_SECRET_KEY", DEFAULT_SECRET)
    BACKEND_URL = backend_url_from_env()
    BACKEND_TIMEOUT = float(os.getenv("MYFILES_BACKEND_TIMEOUT", "30"))
    # um pouco acima do limite do backend, para o backend dar a mensagem de erro
    MAX_CONTENT_LENGTH = (int(os.getenv("MYFILES_MAX_UPLOAD_MB", "50")) + 1) * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True
