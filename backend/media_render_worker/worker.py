"""Цикл воркера: claim -> синтез речи -> липсинк -> заливка в MinIO -> ready/failed.

Один клип — одна попытка за итерацию; при ошибке клип уходит в `failed`
(автор может повторить через POST /clips/{id}/retry в media_service).
Если сам вызов mark_failed не дойдёт (сеть отвалилась именно на этом шаге) —
клип так и останется в `processing` навсегда: retry в media_service работает
только из `failed`. Ручного восстановления на этот случай нет — осознанно
отложено, как и очередь с повторами (см. README, «Дальше»)."""

import logging
import time
from typing import Any

import httpx

from clients import lipsync, media_service, speechkit
from core.config import settings
from core.errors import RenderFailed
from services import photo, storage
from services.photo import PhotoUnreadable
from services.storage import StorageFailed

logger = logging.getLogger(__name__)

# Ошибки, текст которых можно показать автору заявки как есть.
_EXPLAINED = (RenderFailed, PhotoUnreadable, StorageFailed)
# SadTalker оживляет лицо в 256 px и вклеивает его обратно в кадр — фото
# крупнее только раздует загрузку и сам ролик.
_PHOTO_SIDE = 768


def process_one() -> bool:
    """Обрабатывает один клип из очереди. Возвращает False, если очередь пуста."""
    clip = media_service.claim_next()
    if clip is None:
        return False

    clip_id = clip["id"]
    try:
        video = render(clip)
        video_url = storage.upload_video(clip_id=clip_id, content=video)
        media_service.mark_ready(clip_id, video_url=video_url)
        logger.info("Клип %s готов: %s", clip_id, video_url)
    except _EXPLAINED as exc:
        media_service.mark_failed(clip_id, error=str(exc))
        logger.warning("Клип %s: рендер не удался: %s", clip_id, exc)
    except httpx.HTTPError as exc:
        media_service.mark_failed(
            clip_id, error=f"Ошибка внешнего сервиса: {exc.__class__.__name__}"
        )
        logger.warning("Клип %s: сетевая ошибка при рендере: %s", clip_id, exc)
    except Exception:
        # Неожиданное — всё равно отпускаем клип в failed: иначе он навсегда
        # застрянет в processing, и кнопки «Повторить» у автора не будет.
        media_service.mark_failed(clip_id, error="Внутренняя ошибка рендера — попробуйте ещё раз")
        logger.exception("Клип %s: необработанная ошибка рендера", clip_id)
    return True


def render(clip: dict[str, Any]) -> bytes:
    if not settings.render_configured:
        # Без ключа SpeechKit httpx падал на пустом заголовке «Api-Key »
        # (LocalProtocolError) — теперь автор видит, что дело в настройке.
        raise RenderFailed("Оживление фото не настроено: нет ключей SpeechKit и Replicate")
    audio = speechkit.synthesize(clip["narration_text"], clip["voice_style"])
    source = photo.normalize(storage.fetch_source(clip["source_photo_url"]), max_side=_PHOTO_SIDE)
    remote_video_url = lipsync.animate(photo=source, audio_wav=audio)
    return lipsync.download(remote_video_url)


def run_forever() -> None:
    logger.info(
        "Воркер рендера запущен: %s, опрос раз в %.0f сек",
        settings.media_service_url,
        settings.poll_interval_seconds,
    )
    if not settings.render_configured:
        logger.warning("Ключи SpeechKit/Replicate не заданы — заявки будут уходить в failed")
    while True:
        try:
            had_work = process_one()
        except Exception:
            logger.exception("Необработанная ошибка в цикле воркера")
            had_work = False
        if not had_work:
            time.sleep(settings.poll_interval_seconds)
