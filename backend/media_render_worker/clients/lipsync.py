"""Анимация фото под голос — Replicate, модель SadTalker (audio-driven липсинк,
не text-prompt-driven: губы двигаются в такт присланному аудио, не по описанию).

Фото и голос уходят через Files API Replicate, а не ссылками на MinIO: на
стенде MinIO — это IP в локальной сети, Replicate до него не достанет, а
`data:` URI он берёт только до 256 КБ (голос SpeechKit на 48 кГц — ~100 КБ
в секунду). После прогона оба файла удаляем.

Справочник API — https://replicate.com/docs/reference/http."""

import logging
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from core.config import settings
from core.errors import RenderFailed, raise_for_status

__all__ = ["RenderFailed", "animate", "download"]

logger = logging.getLogger(__name__)

_API_BASE = "https://api.replicate.com/v1"
_TERMINAL_STATUSES = {"succeeded", "failed", "canceled"}
_POLL_INTERVAL_SECONDS = 3.0
# Своё имя клиента: API Replicate стоит за Cloudflare, а тот режет запросы по
# подписи — стандартный Python-urllib получает 403 с кодом 1010.
_USER_AGENT = "marshruty-media-render-worker/0.1"

# `full` — лицо оживает, а в кадре остаётся вся фотография (без него в ролике
# только кроп лица 256×256); `still_mode` — голова почти не качается, с `full`
# так и советуют; GFPGAN дочищает лицо после анимации.
_MODEL_INPUT = {
    "preprocess": "full",
    "still_mode": True,
    "use_enhancer": True,
    "use_eyeblink": True,
}


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.replicate_api_token}",
        "User-Agent": _USER_AGENT,
    }


def animate(*, photo: bytes, audio_wav: bytes) -> str:
    """Запускает SadTalker и ждёт результат (poll). Возвращает URL готового
    видео на стороне Replicate — временный, вызывающий код обязан перезалить
    его в своё хранилище (ссылки Replicate не держатся вечно)."""
    uploaded: list[str] = []
    try:
        photo_file = _upload("photo.jpg", photo, "image/jpeg")
        uploaded.append(photo_file["id"])
        audio_file = _upload("voice.wav", audio_wav, "audio/wav")
        uploaded.append(audio_file["id"])
        return _run(
            {
                "source_image": photo_file["urls"]["get"],
                "driven_audio": audio_file["urls"]["get"],
                **_MODEL_INPUT,
            }
        )
    finally:
        for file_id in uploaded:
            _delete(file_id)


def download(url: str) -> bytes:
    """Готовый ролик. Ссылкам на сам API нужен ключ, CDN replicate.delivery — открытый."""
    headers = {"User-Agent": _USER_AGENT}
    if urlsplit(url).hostname == "api.replicate.com":
        headers = _headers()
    response = httpx.get(
        url, headers=headers, timeout=settings.upstream_timeout_seconds, follow_redirects=True
    )
    raise_for_status(response, "Replicate")
    return response.content


def _upload(filename: str, content: bytes, content_type: str) -> dict[str, Any]:
    response = httpx.post(
        f"{_API_BASE}/files",
        headers=_headers(),
        files={"content": (filename, content, content_type)},
        data={"filename": filename, "type": content_type},
        timeout=settings.upstream_timeout_seconds,
    )
    raise_for_status(response, "Replicate")
    return response.json()


def _delete(file_id: str) -> None:
    try:
        httpx.delete(
            f"{_API_BASE}/files/{file_id}",
            headers=_headers(),
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError:
        # Файл истечёт и сам — не повод ронять готовый клип.
        logger.warning("Не удалось удалить файл %s на Replicate", file_id)


def _run(model_input: dict[str, Any]) -> str:
    response = httpx.post(
        f"{_API_BASE}/predictions",
        # Replicate сам отменит прогон по истечении — даже если воркер упадёт.
        headers={**_headers(), "Cancel-After": f"{int(settings.render_timeout_seconds)}s"},
        json={"version": settings.replicate_model_version, "input": model_input},
        timeout=settings.upstream_timeout_seconds,
    )
    raise_for_status(response, "Replicate")
    prediction = response.json()

    deadline = time.monotonic() + settings.render_timeout_seconds
    while prediction["status"] not in _TERMINAL_STATUSES:
        if time.monotonic() > deadline:
            _cancel(prediction)
            raise RenderFailed("Replicate не успел оживить фото — попробуйте ещё раз")
        time.sleep(_POLL_INTERVAL_SECONDS)
        poll = httpx.get(
            prediction["urls"]["get"], headers=_headers(), timeout=settings.upstream_timeout_seconds
        )
        raise_for_status(poll, "Replicate")
        prediction = poll.json()

    if prediction["status"] == "canceled":
        raise RenderFailed("Рендер на Replicate отменён — попробуйте ещё раз")
    if prediction["status"] != "succeeded":
        raise RenderFailed(_explain(prediction.get("error")))

    output = prediction["output"]
    return output if isinstance(output, str) else output[0]


def _cancel(prediction: dict[str, Any]) -> None:
    url = (prediction.get("urls") or {}).get("cancel") or (
        f"{_API_BASE}/predictions/{prediction['id']}/cancel"
    )
    try:
        httpx.post(url, headers=_headers(), timeout=settings.upstream_timeout_seconds)
    except httpx.HTTPError:
        logger.warning("Не удалось отменить прогон %s — его отменит Cancel-After", prediction["id"])


def _explain(error: object) -> str:
    text = str(error or "").strip()
    if "face" in text.lower():
        return "На фото не нашлось лица — нужен портрет, где лицо видно анфас"
    if text:
        return f"Replicate не смог оживить фото: {text[:300]}"
    return "Replicate вернул ошибку рендера"
