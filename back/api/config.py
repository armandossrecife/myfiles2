"""Configuração do backend, lida de variáveis de ambiente.

Nenhum segredo fica no código: em produção, defina pelo menos
MYFILES_SECRET_KEY e MYFILES_DATABASE_URL.
"""
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SECRET = "dev-secret-troque-em-producao-0123456789"


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass
class Settings:
    secret_key: str = DEFAULT_SECRET
    algorithm: str = "HS256"
    token_expire_minutes: int = 30
    database_url: str = "sqlite:///./data/myfiles.db"
    storage_dir: Path = Path("./data")
    max_upload_mb: int = 50
    bcrypt_rounds: int = 12
    # Usuário inicial opcional (útil para demonstrações em sala)
    admin_username: str | None = None
    admin_password: str | None = None
    admin_email: str | None = None

    @property
    def upload_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def profile_dir(self) -> Path:
        return self.storage_dir / "profile"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            secret_key=_env("MYFILES_SECRET_KEY", DEFAULT_SECRET),
            token_expire_minutes=int(_env("MYFILES_TOKEN_EXPIRE_MINUTES", "30")),
            database_url=_env("MYFILES_DATABASE_URL", "sqlite:///./data/myfiles.db"),
            storage_dir=Path(_env("MYFILES_STORAGE_DIR", "./data")),
            max_upload_mb=int(_env("MYFILES_MAX_UPLOAD_MB", "50")),
            bcrypt_rounds=int(_env("MYFILES_BCRYPT_ROUNDS", "12")),
            admin_username=os.getenv("MYFILES_ADMIN_USERNAME"),
            admin_password=os.getenv("MYFILES_ADMIN_PASSWORD"),
            admin_email=os.getenv("MYFILES_ADMIN_EMAIL"),
        )
