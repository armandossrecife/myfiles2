"""Esquemas Pydantic de entrada e saída da API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

USERNAME_PATTERN = r"^[A-Za-z0-9_.-]+$"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=USERNAME_PATTERN)
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    # bcrypt só considera os primeiros 72 bytes
    password: str = Field(min_length=6, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str


class ProfileOut(UserOut):
    profile_image_url: str
    has_custom_image: bool


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NoteIn(BaseModel):
    description: str = Field(min_length=1, max_length=1024)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    created_at: datetime
    updated_at: datetime


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    media_type: str
    size: int
    uploaded_at: datetime


class Message(BaseModel):
    message: str


class TimelineItem(BaseModel):
    Task: str
    Start: str
    Finish: str


class TaskOut(BaseModel):
    descricao: str
    data_expiracao: str
    prioridade: int
    concluida: bool
