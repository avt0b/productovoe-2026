"""Анимация фото под голос — Replicate, модель SadTalker (audio-driven липсинк,
не text-prompt-driven: губы двигаются в такт присланному аудио, не по описанию)."""

import time

import httpx

from core.config import settings

_API_BASE = "https://api.replicate.com/v1"
_TERMINAL_STATUSES = {"succeeded", "failed", "canceled"}
_POLL_INTERVAL_SECONDS = 3.0


class RenderFailed(Exception):
    """Replicate вернул ошибку или не уложился в таймаут."""


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.replicate_api_token}",
        "Content-Type": "application/json",
    }


def animate(*, photo_url: str, audio_data_uri: str) -> str:
    """Запускает SadTalker и ждёт результат (poll). Возвращает URL готового
    видео на стороне Replicate — временный, вызывающий код обязан перезалить
    его в своё хранилище (ссылки Replicate не держатся вечно)."""
    response = httpx.post(
        f"{_API_BASE}/predictions",
        headers=_headers(),
        json={
            "version": settings.replicate_model_version,
            "input": {
                "source_image": photo_url,
                "driven_audio": audio_data_uri,
                "still_mode": True,
                "use_enhancer": True,
            },
        },
        timeout=settings.upstream_timeout_seconds,
    )
    response.raise_for_status()
    prediction = response.json()

    deadline = time.monotonic() + settings.render_timeout_seconds
    while prediction["status"] not in _TERMINAL_STATUSES:
        if time.monotonic() > deadline:
            raise RenderFailed("Превышено время ожидания рендера на Replicate")
        time.sleep(_POLL_INTERVAL_SECONDS)
        poll = httpx.get(
            prediction["urls"]["get"], headers=_headers(), timeout=settings.upstream_timeout_seconds
        )
        poll.raise_for_status()
        prediction = poll.json()

    if prediction["status"] != "succeeded":
        raise RenderFailed(str(prediction.get("error") or "Replicate вернул ошибку рендера"))

    output = prediction["output"]
    return output if isinstance(output, str) else output[0]
