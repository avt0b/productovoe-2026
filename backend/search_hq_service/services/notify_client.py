"""Клиент внутренней ручки user_service `/internal/notifications/send`.

user_service недоступен — не роняем открытие сбора: краевед уже стоит на месте,
и группа всё равно увидит сбор, открыв экскурсию. Уведомление — удобство, а не
условие. Синхронный вызов, как award_achievement: побочный эффект внутри уже
синхронного метода сервиса.
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def notify_users(
    *, user_ids: list[str], kind: str, title: str, body: str, payload: dict | None = None
) -> None:
    if not user_ids:
        return
    try:
        response = httpx.post(
            f"{settings.user_service_url}/internal/notifications/send",
            headers={"X-Internal-Key": settings.internal_api_key},
            json={"user_ids": user_ids, "kind": kind, "title": title, "body": body, "payload": payload},
            timeout=settings.upstream_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("user_service недоступен для notifications/send: %s", exc)
