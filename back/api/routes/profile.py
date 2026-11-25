from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api import armazenamento, banco, entidades, modelos, seguranca
from api.config import Settings

router = APIRouter(tags=["perfil"])

DEFAULT_IMAGE = Path(__file__).resolve().parent.parent / "static" / "default.png"


def _profile(user: modelos.UserDB) -> entidades.ProfileOut:
    return entidades.ProfileOut(
        id=user.id,
        username=user.username,
        email=user.email,
        profile_image_url=f"/users/{user.username}/profile/image",
        has_custom_image=user.profile_image is not None,
    )


@router.get("/users/{username}/profile", response_model=entidades.ProfileOut)
def read_profile(owner: modelos.UserDB = Depends(seguranca.get_owner)):
    return _profile(owner)


@router.get("/users/{username}/profile/image", response_class=FileResponse)
def read_profile_image(
    owner: modelos.UserDB = Depends(seguranca.get_owner),
    settings: Settings = Depends(seguranca.get_settings),
):
    if owner.profile_image:
        path = armazenamento.safe_path(settings.profile_dir, owner.profile_image)
        if path.exists():
            media_type = armazenamento.MEDIA_TYPES[armazenamento.get_extension(path.name)]
            return FileResponse(path, media_type=media_type)
    return FileResponse(DEFAULT_IMAGE, media_type="image/png")


@router.post("/users/{username}/profile/image", response_model=entidades.ProfileOut)
async def upload_profile_image(
    request: Request,
    image: UploadFile = File(...),
    owner: modelos.UserDB = Depends(seguranca.get_owner),
    db: Session = Depends(banco.get_db),
    settings: Settings = Depends(seguranca.get_settings),
):
    ext = armazenamento.validate_extension(image.filename, armazenamento.PROFILE_EXTENSIONS)
    stored_name, _ = await armazenamento.save_upload(
        image, settings.profile_dir, ext, settings.max_upload_bytes
    )
    # owner veio de outra sessão (dependência); recarrega nesta sessão
    user = db.merge(owner)
    old_image = user.profile_image
    banco.UserDAO(db).set_profile_image(user, stored_name)
    if old_image:
        armazenamento.remove_file(settings.profile_dir, old_image)
    return _profile(user)
