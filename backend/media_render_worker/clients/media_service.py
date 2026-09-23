"""Клиент очереди media_service (`/render/*`, `X-Worker-Token`).

Пул-модель, не push: воркер сам спрашивает, есть ли работа, а не ждёт
уведомления — так же, как /excursions/{id}/gathering в search_hq_service
опрашивается с телефона, без WebSocket."""

from http import HTTPStatus
from typing import Any

import httpx

from core.config import settings


def _headers() -> dict[str, str]:
    return {"X-Worker-Token": settings.render_worker_token}


def claim_next() -> dict[str, Any] | None:
    """Взять самый старый клип из очереди: queued -> processing. None — очередь пуста."""
    response = httpx.post(
        f"{settings.media_service_url}/render/claim",
        headers=_headers(),
        timeout=settings.upstream_timeout_seconds,
    )
    response.raise_for_status()
    if response.status_code == HTTPStatus.NO_CONTENT:
        return None
    return response.json()


def mark_ready(clip_id: str, *, video_url: str) -> None:
    response = httpx.post(
        f"{settings.media_service_url}/render/{clip_id}/ready",
        headers=_headers(),
        json={"video_url": video_url},
        timeout=settings.upstream_timeout_seconds,
    )
    response.raise_for_status()


def mark_failed(clip_id: str, *, error: str) -> None:
    response = httpx.post(
        f"{settings.media_service_url}/render/{clip_id}/failed",
        headers=_headers(),
        json={"error": error[:1000]},
        timeout=settings.upstream_timeout_seconds,
    )
    response.raise_for_status()
