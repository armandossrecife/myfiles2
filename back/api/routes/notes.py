from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from api import banco, entidades, modelos, seguranca

router = APIRouter(prefix="/users/{username}/notes", tags=["anotações"])


def _get_note_or_404(dao: banco.NoteDAO, note_id: int, owner: modelos.UserDB) -> modelos.NoteDB:
    note = dao.get(note_id, owner.id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anotação não encontrada")
    return note


@router.get("", response_model=list[entidades.NoteOut])
def list_notes(owner: modelos.UserDB = Depends(seguranca.get_owner), db: Session = Depends(banco.get_db)):
    return banco.NoteDAO(db).list_by_user(owner.id)


@router.post("", response_model=entidades.NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    data: entidades.NoteIn,
    owner: modelos.UserDB = Depends(seguranca.get_owner),
    db: Session = Depends(banco.get_db),
):
    return banco.NoteDAO(db).create(owner.id, data.description)


@router.get("/{note_id}", response_model=entidades.NoteOut)
def read_note(note_id: int, owner: modelos.UserDB = Depends(seguranca.get_owner), db: Session = Depends(banco.get_db)):
    return _get_note_or_404(banco.NoteDAO(db), note_id, owner)


@router.put("/{note_id}", response_model=entidades.NoteOut)
def update_note(
    note_id: int,
    data: entidades.NoteIn,
    owner: modelos.UserDB = Depends(seguranca.get_owner),
    db: Session = Depends(banco.get_db),
):
    dao = banco.NoteDAO(db)
    return dao.update(_get_note_or_404(dao, note_id, owner), data.description)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, owner: modelos.UserDB = Depends(seguranca.get_owner), db: Session = Depends(banco.get_db)):
    dao = banco.NoteDAO(db)
    dao.delete(_get_note_or_404(dao, note_id, owner))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
