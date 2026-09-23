"""Клиент публичной ручки media_service `/clips` (фильтр по `poi_id`).

media_service недоступен — не роняем показ маршрута: подсказка «оживить
фото» просто не появится (см. MediaPromptService).
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


async def has_public_clip(poi_id: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
            response = await client.get(
                f"{settings.media_service_url}/clips", params={"poi_id": poi_id, "limit": 1}
            )
            response.raise_for_status()
            return len(response.json()) > 0
    except httpx.HTTPError as exc:
        logger.warning("media_service недоступен для clips?poi_id=%s: %s", poi_id, exc)
        # Недоступность сервиса — не повод утверждать «клипа нет»: молчим.
        return True
