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
    # Какой шаг идёт — чтобы в ошибке было видно, что именно сломалось, а не
    # «HTTPStatusError» без подробностей.
    step = "Озвучка текста (Yandex SpeechKit)"
    try:
        text = _limit_narration(clip["narration_text"], settings.max_narration_chars)
        voice = speechkit.synthesize(text, clip["voice_style"])
        step = "Загрузка фото героя"
        # Фото качаем сами и шлём данными: Ranvik не нужен доступ к нашему MinIO.
        photo = _fetch_photo(clip["source_photo_url"])

        step = "Оживление фото (Ranvik)"
        video_bytes = ranvik.animate(photo=photo, voice_wav=voice)
        step = "Сохранение ролика"
        video_url = storage.upload_video(clip_id=clip_id, content=video_bytes)

        media_service.mark_ready(clip_id, video_url=video_url)
        logger.info("Клип %s готов: %s", clip_id, video_url)
    except RenderFailed as exc:
        media_service.mark_failed(clip_id, error=str(exc))
        logger.warning("Клип %s: рендер не удался: %s", clip_id, exc)
    except httpx.HTTPError as exc:
        error = f"{step}: {_describe_http_error(exc)}"
        media_service.mark_failed(clip_id, error=error)
        logger.warning("Клип %s: %s (%s: %s)", clip_id, error, exc.__class__.__name__, exc)
    return True


def _describe_http_error(exc: httpx.HTTPError) -> str:
    """Почему не ответил внешний сервис — словами, которые поймёт автор клипа."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status in (401, 403):
            return f"сервис не принял ключ доступа ({status})"
        if status == 402:
            return "на счёте сервиса закончились деньги (402)"
        if status == 429:
            return "сервис перегружен запросами, попробуйте позже (429)"
        if status >= 500:
            return f"сбой на стороне сервиса ({status}), попробуйте позже"
        return f"сервис ответил ошибкой {status}"
    if isinstance(exc, httpx.TimeoutException):
        return "сервис не ответил вовремя"
    if isinstance(exc, httpx.TransportError):
        return "не удалось подключиться к сервису"
    return exc.__class__.__name__


def _fetch_photo(url: str) -> bytes:
    """Фото из нашего MinIO читаем по S3 изнутри сети, чужое — качаем по ссылке."""
    own = storage.own_object(url)
    if own is not None:
        return storage.read_object(*own)
    return _download(url)


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
