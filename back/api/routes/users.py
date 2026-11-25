from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api import banco, entidades, modelos, seguranca
from api.config import Settings

router = APIRouter(tags=["usuários"])


@router.post("/users", response_model=entidades.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: entidades.UserCreate,
    db: Session = Depends(banco.get_db),
    settings: Settings = Depends(seguranca.get_settings),
):
    dao = banco.UserDAO(db)
    if dao.get_by_username(data.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome de usuário já cadastrado")
    if dao.get_by_email(data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado")
    password_hash = seguranca.hash_password(data.password, settings.bcrypt_rounds)
    return dao.create(data.username, data.email, password_hash)


@router.get("/users/me", response_model=entidades.UserOut)
def read_me(current: modelos.UserDB = Depends(seguranca.get_current_user)):
    return current


@router.get("/users/{username}", response_model=entidades.UserOut)
def read_user(owner: modelos.UserDB = Depends(seguranca.get_owner)):
    return owner
