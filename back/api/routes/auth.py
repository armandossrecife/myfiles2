from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api import banco, entidades, modelos, seguranca
from api.config import Settings

router = APIRouter(tags=["autenticação"])


def _authenticate(db: Session, settings: Settings, username: str, password: str) -> entidades.Token:
    user = banco.UserDAO(db).get_by_username(username)
    if user is None or not seguranca.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return entidades.Token(access_token=seguranca.create_access_token(user.username, settings))


@router.post("/login", response_model=entidades.Token)
def login(
    credentials: entidades.UserLogin,
    db: Session = Depends(banco.get_db),
    settings: Settings = Depends(seguranca.get_settings),
):
    """Login com JSON {username, password}. Usado pelo frontend."""
    return _authenticate(db, settings, credentials.username, credentials.password)


@router.post("/token", response_model=entidades.Token, include_in_schema=False)
def token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(banco.get_db),
    settings: Settings = Depends(seguranca.get_settings),
):
    """Login no formato OAuth2 (formulário). Usado pelo botão Authorize do /docs."""
    return _authenticate(db, settings, form.username, form.password)


@router.post("/logout", response_model=entidades.Message)
def logout(_: modelos.UserDB = Depends(seguranca.get_current_user)):
    """O JWT é stateless: o cliente apenas descarta o token, que expira sozinho."""
    return {"message": "Logout realizado"}
