"""Regras de tipos de arquivo e gravação segura no disco."""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

MEDIA_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "mp4": "video/mp4",
    "mp3": "audio/mpeg",
}
PROFILE_EXTENSIONS = {"jpg", "jpeg", "png"}
CHUNK_SIZE = 1024 * 1024


def get_extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def validate_extension(filename: str | None, allowed: set[str]) -> str:
    ext = get_extension(filename)
    if ext not in allowed:
        permitidas = ", ".join(sorted(allowed))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido. Extensões aceitas: {permitidas}",
        )
    return ext


def safe_path(directory: Path, name: str) -> Path:
    """Resolve name dentro de directory, recusando qualquer fuga (path traversal)."""
    base = directory.resolve()
    target = (base / name).resolve()
    if target.parent != base:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nome de arquivo inválido")
    return target


async def save_upload(upload: UploadFile, directory: Path, extension: str, max_bytes: int) -> tuple[str, int]:
    """Grava o upload em blocos com nome UUID. Devolve (nome_gravado, tamanho)."""
    directory.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.{extension}"
    destination = safe_path(directory, stored_name)
    size = 0
    try:
        with destination.open("wb") as out:
            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"Arquivo maior que o limite de {max_bytes // (1024 * 1024)} MB",
                    )
                out.write(chunk)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio")
    return stored_name, size


def remove_file(directory: Path, name: str) -> None:
    safe_path(directory, name).unlink(missing_ok=True)
