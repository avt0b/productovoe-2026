"""Цикл воркера: claim -> оживление фото -> заливка в MinIO -> ready/failed.

Оживляет один из двух провайдеров (`RENDER_PROVIDER`, по умолчанию `auto`):
- **Ranvik** — беззвучно, несколько секунд: моргнёт, вздохнёт, повернёт голову;
  берётся, если задан `RANVIK_API_KEY`;
- **SpeechKit + Replicate** — голос от первого лица и липсинк SadTalker.

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

from clients import lipsync, media_service, ranvik, speechkit
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
# Видеомодели Ranvik рисуют весь кадр в 720p — фото нужно почётче.
_RANVIK_PHOTO_SIDE = 1280


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
    provider = settings.effective_render_provider
    if provider is None:
        # Без ключа SpeechKit httpx падал на пустом заголовке «Api-Key »
        # (LocalProtocolError) — теперь автор видит, что дело в настройке.
        raise RenderFailed(
            "Оживление фото не настроено: нет ключа Ranvik или ключей SpeechKit и Replicate"
        )
    if provider == "ranvik":
        source = storage.fetch_source(clip["source_photo_url"])
        return ranvik.animate(photo=photo.normalize(source, max_side=_RANVIK_PHOTO_SIDE))
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
    provider = settings.effective_render_provider
    if provider is None:
        logger.warning(
            "Ключи Ranvik и SpeechKit/Replicate не заданы — заявки будут уходить в failed"
        )
    else:
        logger.info("Оживление фото: %s", provider)
    while True:
        try:
            had_work = process_one()
        except Exception:
            logger.exception("Необработанная ошибка в цикле воркера")
            had_work = False
        if not had_work:
            time.sleep(settings.poll_interval_seconds)
