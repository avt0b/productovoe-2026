"""Клиент внутренней ручки user_service `/internal/stats/increment`.

Та же fire-and-forget логика, что у achievement_client.py: user_service
недоступен — не роняем завершение маршрута, счётчик просто не увеличится
сейчас. В отличие от ачивок — не идемпотентно, каждый вызов прибавляет 1,
так что дёргать нужно ровно один раз на событие (см. ProgressService)."""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def increment_stat(*, user_id: str, metric: str) -> None:
    try:
        response = httpx.post(
            f"{settings.user_service_url}/internal/stats/increment",
            headers={"X-Internal-Key": settings.internal_api_key},
            json={"user_id": user_id, "metric": metric},
            timeout=settings.upstream_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("user_service недоступен для stats/increment: %s", exc)
