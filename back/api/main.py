"""Fábrica da aplicação FastAPI."""
import logging

from fastapi import FastAPI

from api import banco, seguranca
from api.config import DEFAULT_SECRET, Settings
from api.routes import auth, charts, files, notes, profile, users

logger = logging.getLogger("myfiles.api")


def _seed_admin(app: FastAPI, settings: Settings) -> None:
    if not (settings.admin_username and settings.admin_password and settings.admin_email):
        return
    with app.state.session_factory() as db:
        dao = banco.UserDAO(db)
        if dao.get_by_username(settings.admin_username) is None:
            dao.create(
                settings.admin_username,
                settings.admin_email,
                seguranca.hash_password(settings.admin_password, settings.bcrypt_rounds),
            )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    if settings.secret_key == DEFAULT_SECRET:
        logger.warning("MYFILES_SECRET_KEY não definida: usando chave de desenvolvimento.")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.profile_dir.mkdir(parents=True, exist_ok=True)

    engine = banco.build_engine(settings.database_url)
    banco.create_tables(engine)

    app = FastAPI(
        title="MyFiles API",
        description="Usuários, anotações e arquivos de mídia (imagem, vídeo e áudio).",
        version="2.0.0",
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = banco.make_session_factory(engine)

    @app.get("/health", tags=["infra"])
    def health():
        return {"status": "ok"}

    for module in (auth, users, profile, notes, files, charts):
        app.include_router(module.router)

    _seed_admin(app, settings)
    return app
