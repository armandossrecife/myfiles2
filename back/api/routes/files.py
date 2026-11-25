from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api import armazenamento, banco, entidades, modelos, seguranca
from api.config import Settings

router = APIRouter(prefix="/users/{username}/files", tags=["arquivos"])


def _get_file_or_404(dao: banco.FileDAO, file_id: int, owner: modelos.UserDB) -> modelos.MediaFileDB:
    media = dao.get(file_id, owner.id)
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado")
    return media


@router.get("", response_model=list[entidades.FileOut])
def list_files(owner: modelos.UserDB = Depends(seguranca.get_owner), db: Session = Depends(banco.get_db)):
    return banco.FileDAO(db).list_by_user(owner.id)


@router.post("", response_model=entidades.FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    owner: modelos.UserDB = Depends(seguranca.get_owner),
    db: Session = Depends(banco.get_db),
    settings: Settings = Depends(seguranca.get_settings),
):
    ext = armazenamento.validate_extension(file.filename, set(armazenamento.MEDIA_TYPES))
    stored_name, size = await armazenamento.save_upload(file, settings.upload_dir, ext, settings.max_upload_bytes)
    try:
        return banco.FileDAO(db).create(
            user_id=owner.id,
            original_name=file.filename,
            stored_name=stored_name,
            media_type=armazenamento.MEDIA_TYPES[ext],
            size=size,
        )
    except Exception:
        armazenamento.remove_file(settings.upload_dir, stored_name)
        raise


@router.get("/{file_id}", response_model=entidades.FileOut)
def read_file(file_id: int, owner: modelos.UserDB = Depends(seguranca.get_owner), db: Session = Depends(banco.get_db)):
    return _get_file_or_404(banco.FileDAO(db), file_id, owner)


@router.get("/{file_id}/content", response_class=FileResponse)
def download_file(
    file_id: int,
    owner: modelos.UserDB = Depends(seguranca.get_owner),
    db: Session = Depends(banco.get_db),
    settings: Settings = Depends(seguranca.get_settings),
):
    media = _get_file_or_404(banco.FileDAO(db), file_id, owner)
    path = armazenamento.safe_path(settings.upload_dir, media.stored_name)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conteúdo do arquivo não encontrado")
    return FileResponse(
        path,
        media_type=media.media_type,
        filename=media.original_name,
        content_disposition_type="inline",
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: int,
    owner: modelos.UserDB = Depends(seguranca.get_owner),
    db: Session = Depends(banco.get_db),
    settings: Settings = Depends(seguranca.get_settings),
):
    dao = banco.FileDAO(db)
    media = _get_file_or_404(dao, file_id, owner)
    stored_name = media.stored_name
    dao.delete(media)
    armazenamento.remove_file(settings.upload_dir, stored_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
