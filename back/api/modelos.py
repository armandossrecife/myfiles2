"""Tabelas do banco (SQLAlchemy 2.x)."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # Nome do arquivo da foto de perfil dentro de storage/profile (None = foto padrão)
    profile_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    notes: Mapped[list["NoteDB"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    files: Mapped[list["MediaFileDB"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class NoteDB(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(String(1024))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)

    owner: Mapped[UserDB] = relationship(back_populates="notes")


class MediaFileDB(Base):
    """Arquivo de mídia enviado por um usuário.

    O conteúdo fica no disco com um nome UUID (stored_name); o nome original
    só é guardado para exibição.
    """
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    media_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    owner: Mapped[UserDB] = relationship(back_populates="files")
