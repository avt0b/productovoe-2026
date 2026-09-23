"""Клиент внутренней ручки user_service `/internal/notifications/broadcast-nearby`.

user_service недоступен — не роняем создание точки «Последнего боя»: уведомления
просто не разойдутся сейчас (см. LastStandService.create).
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def notify_nearby_subscribers(*, lat: float, lon: float, title: str, body: str) -> None:
    try:
        httpx.post(
            f"{settings.user_service_url}/internal/notifications/broadcast-nearby",
            headers={"X-Internal-Key": settings.internal_api_key},
            json={
                "lat": lat,
                "lon": lon,
                "kind": "last_stand_nearby",
                "title": title,
                "body": body,
            },
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        logger.warning("user_service недоступен для broadcast-nearby: %s", exc)
