"""Цикл воркера: claim -> синтез речи -> говорящий портрет (фото + голос) ->
заливка в MinIO -> ready/failed.

Один клип — одна попытка за итерацию; при ошибке клип уходит в `failed`
(автор может повторить через POST /clips/{id}/retry в media_service).
Если сам вызов mark_failed не дойдёт (сеть отвалилась именно на этом шаге) —
клип так и останется в `processing` навсегда: retry в media_service работает
только из `failed`. Ручного восстановления на этот случай нет — осознанно
отложено, как и очередь с повторами (см. README, «Дальше»)."""

import logging
import re
import time

import httpx

from clients import media_service, ranvik, speechkit
from core.config import settings
from core.exceptions import RenderFailed
from services import storage

logger = logging.getLogger(__name__)


def process_one() -> bool:
    """Обрабатывает один клип из очереди. Возвращает False, если очередь пуста."""
    clip = media_service.claim_next()
    if clip is None:
        return False

    clip_id = clip["id"]
    try:
        text = _limit_narration(clip["narration_text"], settings.max_narration_chars)
        voice = speechkit.synthesize(text, clip["voice_style"])
        # Фото качаем сами и шлём данными: Ranvik не нужен доступ к нашему MinIO.
        photo = _download(clip["source_photo_url"])

        video_bytes = ranvik.animate(photo=photo, voice_wav=voice)
        video_url = storage.upload_video(clip_id=clip_id, content=video_bytes)

        media_service.mark_ready(clip_id, video_url=video_url)
        logger.info("Клип %s готов: %s", clip_id, video_url)
    except RenderFailed as exc:
        media_service.mark_failed(clip_id, error=str(exc))
        logger.warning("Клип %s: рендер не удался: %s", clip_id, exc)
    except httpx.HTTPError as exc:
        media_service.mark_failed(
            clip_id, error=f"Ошибка внешнего сервиса: {exc.__class__.__name__}"
        )
        logger.warning("Клип %s: сетевая ошибка при рендере: %s", clip_id, exc)
    return True


def _limit_narration(text: str, max_chars: int) -> str:
    """Текст не длиннее max_chars — обрезка по концу предложения, чтобы речь не
    обрывалась на полуслове. Платим за каждую секунду голоса (см. config)."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    head = text[:max_chars]
    sentence_ends = [m.end() for m in re.finditer(r"[.!?…]+", head)]
    if sentence_ends:
        return head[: sentence_ends[-1]].strip()
    # Одно длинное предложение — режем по последнему целому слову (+1 символ,
    # чтобы слово, кончающееся ровно на границе, не потерялось).
    return text[: max_chars + 1].rsplit(" ", 1)[0].rstrip(",;:—- ") + "…"


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
