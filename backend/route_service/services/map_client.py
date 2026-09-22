"""Клиент публичной ручки map_service `/poi/nearby`.

map_service недоступен — не роняем автогенерацию: она просто вернёт ошибку
«нет точек рядом» вместо маршрута (см. RouteService.auto_generate).
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


async def fetch_poi_nearby(
    *, lat: float, lon: float, radius_km: float, kind: str | None = None, limit: int = 50
) -> list[dict]:
    params: dict[str, float | int | str] = {"lat": lat, "lon": lon, "radius_km": radius_km, "limit": limit}
    if kind:
        params["kind"] = kind
    try:
        async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
            response = await client.get(f"{settings.map_service_url}/poi/nearby", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("map_service недоступен для poi/nearby: %s", exc)
        return []
