"""Клиент публичной ручки archive_service `/entries/{id}`.

archive_service недоступен или запись не найдена/не подтверждена — не роняем
создание заявки: текст подвига просто не подтянется, останется дефолтный
монолог (см. ClipService.create).
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


async def fetch_entry(entry_id: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
            response = await client.get(f"{settings.archive_service_url}/entries/{entry_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("archive_service недоступен для entries/%s: %s", entry_id, exc)
        return None
