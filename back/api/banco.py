"""Acesso ao banco: criação do engine, sessão por requisição e DAOs."""
from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from api import modelos


def build_engine(database_url: str) -> Engine:
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # garante que a pasta do arquivo .db exista
        db_path = database_url.split("///", 1)[-1]
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url, connect_args=connect_args)


def create_tables(engine: Engine) -> None:
    """Cria as tabelas que ainda não existem (nunca apaga dados)."""
    modelos.Base.metadata.create_all(bind=engine)


def get_db(request: Request):
    """Dependência do FastAPI: uma sessão por requisição."""
    db: Session = request.app.state.session_factory()
    try:
        yield db
    finally:
        db.close()


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class UserDAO:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> modelos.UserDB | None:
        return self.db.scalar(select(modelos.UserDB).where(modelos.UserDB.username == username))

    def get_by_email(self, email: str) -> modelos.UserDB | None:
        return self.db.scalar(select(modelos.UserDB).where(modelos.UserDB.email == email))

    def create(self, username: str, email: str, password_hash: str) -> modelos.UserDB:
        user = modelos.UserDB(username=username, email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_profile_image(self, user: modelos.UserDB, filename: str | None) -> None:
        user.profile_image = filename
        self.db.commit()


class NoteDAO:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[modelos.NoteDB]:
        stmt = select(modelos.NoteDB).where(modelos.NoteDB.user_id == user_id).order_by(modelos.NoteDB.id)
        return list(self.db.scalars(stmt))

    def get(self, note_id: int, user_id: int) -> modelos.NoteDB | None:
        """Só encontra a nota se ela pertencer ao usuário."""
        stmt = select(modelos.NoteDB).where(modelos.NoteDB.id == note_id, modelos.NoteDB.user_id == user_id)
        return self.db.scalar(stmt)

    def create(self, user_id: int, description: str) -> modelos.NoteDB:
        note = modelos.NoteDB(user_id=user_id, description=description)
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def update(self, note: modelos.NoteDB, description: str) -> modelos.NoteDB:
        note.description = description
        self.db.commit()
        self.db.refresh(note)
        return note

    def delete(self, note: modelos.NoteDB) -> None:
        self.db.delete(note)
        self.db.commit()


class FileDAO:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[modelos.MediaFileDB]:
        stmt = (
            select(modelos.MediaFileDB)
            .where(modelos.MediaFileDB.user_id == user_id)
            .order_by(modelos.MediaFileDB.id)
        )
        return list(self.db.scalars(stmt))

    def get(self, file_id: int, user_id: int) -> modelos.MediaFileDB | None:
        stmt = select(modelos.MediaFileDB).where(
            modelos.MediaFileDB.id == file_id, modelos.MediaFileDB.user_id == user_id
        )
        return self.db.scalar(stmt)

    def create(self, user_id: int, original_name: str, stored_name: str, media_type: str, size: int):
        media = modelos.MediaFileDB(
            user_id=user_id,
            original_name=original_name,
            stored_name=stored_name,
            media_type=media_type,
            size=size,
        )
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        return media

    def delete(self, media: modelos.MediaFileDB) -> None:
        self.db.delete(media)
        self.db.commit()
