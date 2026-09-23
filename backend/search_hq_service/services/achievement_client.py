"""Клиент внутренней ручки user_service `/internal/achievements/award`.

user_service недоступен — не роняем регистрацию на выезд или донат: ачивка
просто не выдастся сейчас (см. TripService.register, NeedService.donate/
confirm_payment). Синхронный вызов — fire-and-forget побочный эффект
внутри уже синхронного метода сервиса, как notify_nearby_subscribers в
map_service.
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def award_achievement(*, user_id: str, code: str) -> None:
    try:
        response = httpx.post(
            f"{settings.user_service_url}/internal/achievements/award",
            headers={"X-Internal-Key": settings.internal_api_key},
            json={"user_id": user_id, "code": code},
            timeout=settings.upstream_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("user_service недоступен для achievements/award: %s", exc)
