"""Цикл воркера: claim -> синтез речи -> липсинк -> заливка в MinIO -> ready/failed.

Один клип — одна попытка за итерацию; при ошибке клип уходит в `failed`
(автор может повторить через POST /clips/{id}/retry в media_service).
Если сам вызов mark_failed не дойдёт (сеть отвалилась именно на этом шаге) —
клип так и останется в `processing` навсегда: retry в media_service работает
только из `failed`. Ручного восстановления на этот случай нет — осознанно
отложено, как и очередь с повторами (см. README, «Дальше»)."""

import base64
import logging
import time

import httpx

from clients import lipsync, media_service, speechkit
from clients.lipsync import RenderFailed
from core.config import settings
from services import storage

logger = logging.getLogger(__name__)


def process_one() -> bool:
    """Обрабатывает один клип из очереди. Возвращает False, если очередь пуста."""
    clip = media_service.claim_next()
    if clip is None:
        return False

    clip_id = clip["id"]
    try:
        audio = speechkit.synthesize(clip["narration_text"], clip["voice_style"])
        audio_data_uri = "data:audio/wav;base64," + base64.b64encode(audio).decode()

        remote_video_url = lipsync.animate(
            photo_url=clip["source_photo_url"], audio_data_uri=audio_data_uri
        )
        video_bytes = _download(remote_video_url)
        video_url = storage.upload_video(clip_id=clip_id, content=video_bytes)

        media_service.mark_ready(clip_id, video_url=video_url)
        logger.info("Клип %s готов: %s", clip_id, video_url)
    except RenderFailed as exc:
        media_service.mark_failed(clip_id, error=str(exc))
        logger.warning("Клип %s: рендер не удался: %s", clip_id, exc)
    except httpx.HTTPError as exc:
        media_service.mark_failed(clip_id, error=f"Ошибка внешнего сервиса: {exc.__class__.__name__}")
        logger.warning("Клип %s: сетевая ошибка при рендере: %s", clip_id, exc)
    return True


def _download(url: str) -> bytes:
    response = httpx.get(url, timeout=settings.upstream_timeout_seconds)
    response.raise_for_status()
    return response.content


def run_forever() -> None:
    logger.info(
        "Воркер рендера запущен: %s, опрос раз в %.0f сек",
        settings.media_service_url,
        settings.poll_interval_seconds,
    )
    while True:
        try:
            had_work = process_one()
        except Exception:
            logger.exception("Необработанная ошибка в цикле воркера")
            had_work = False
        if not had_work:
            time.sleep(settings.poll_interval_seconds)
