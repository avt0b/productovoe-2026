from fastapi import APIRouter, HTTPException, UploadFile, status

from api.deps import CurrentPrincipal
from services import storage

router = APIRouter(prefix="/uploads", tags=["uploads (фото бойца, фото и аудио к записям архива)"])

IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
# Аудиовоспоминания «Живой памяти» (модуль 6 ТЗ). Браузеры по-разному называют
# WAV и M4A, а запись с микрофона (MediaRecorder) в Chrome приходит как webm.
AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm",
}
ALLOWED_CONTENT_TYPES = IMAGE_CONTENT_TYPES | AUDIO_CONTENT_TYPES

MAX_IMAGE_BYTES = 15 * 1024 * 1024
# Голосовое воспоминание длиннее и тяжелее фото.
MAX_AUDIO_BYTES = 30 * 1024 * 1024


@router.post("")
async def upload_file(principal: CurrentPrincipal, file: UploadFile) -> dict:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Допустимы изображения (JPEG, PNG, WebP) или аудио (MP3, OGG, WAV, M4A, WebM)",
        )
    is_audio = file.content_type in AUDIO_CONTENT_TYPES
    max_bytes = MAX_AUDIO_BYTES if is_audio else MAX_IMAGE_BYTES
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, f"Файл больше {max_bytes // (1024 * 1024)} МБ"
        )

    url = storage.upload(
        key_prefix=principal.user_id,
        filename=file.filename or ("audio" if is_audio else "photo"),
        content=content,
        content_type=file.content_type,
    )
    return {"url": url}
