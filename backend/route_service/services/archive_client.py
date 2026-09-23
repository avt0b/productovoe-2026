"""Клиент публичной ручки archive_service `/entries/nearby-pending`.

Архив недоступен — не роняем показ маршрута: подсказка «помоги проверить»
просто не появится (см. ArchivePromptService).
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


async def fetch_nearby_pending(
    bbox: tuple[float, float, float, float], *, limit: int = 100
) -> list[dict]:
    min_lat, min_lon, max_lat, max_lon = bbox
    try:
        async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
            response = await client.get(
                f"{settings.archive_service_url}/entries/nearby-pending",
                params={
                    "min_lat": min_lat,
                    "min_lon": min_lon,
                    "max_lat": max_lat,
                    "max_lon": max_lon,
                    "limit": limit,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("archive_service недоступен для nearby-pending: %s", exc)
        return []
