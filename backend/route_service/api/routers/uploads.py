from fastapi import APIRouter, HTTPException, UploadFile, status

from api.deps import CurrentPrincipal
from services import storage

router = APIRouter(prefix="/uploads", tags=["uploads (обложки маршрутов, аудио точек)"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "audio/mpeg",
    "audio/ogg",
    "audio/mp4",
    "audio/wav",
}


@router.post("")
async def upload_file(principal: CurrentPrincipal, file: UploadFile) -> dict:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Допустимы изображения (JPEG/PNG/WebP) или аудио (MP3/OGG/M4A/WAV)",
        )
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Файл больше 20 МБ")

    url = storage.upload(
        key_prefix=principal.user_id,
        filename=file.filename or "file",
        content=content,
        content_type=file.content_type,
    )
    return {"url": url}
