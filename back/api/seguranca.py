"""Senhas (bcrypt), tokens JWT e as dependências de autenticação/autorização."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api import banco, modelos
from api.config import Settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def hash_password(password: str, rounds: int = 12) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(username: str, settings: Settings, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.token_expire_minutes))
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, settings: Settings) -> str:
    """Devolve o username do token ou lança jwt.InvalidTokenError."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    username = payload.get("sub")
    if not username:
        raise jwt.InvalidTokenError("token sem 'sub'")
    return username


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(banco.get_db),
    settings: Settings = Depends(get_settings),
) -> modelos.UserDB:
    try:
        username = decode_token(token, settings)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token expirado")
    except jwt.InvalidTokenError:
        raise _unauthorized("Token inválido")
    user = banco.UserDAO(db).get_by_username(username)
    if user is None:
        raise _unauthorized("Usuário do token não existe")
    return user


async def get_owner(username: str, current: modelos.UserDB = Depends(get_current_user)) -> modelos.UserDB:
    """Autorização: o {username} da URL precisa ser o dono do token."""
    if current.username != username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a dados de outro usuário")
    return current
