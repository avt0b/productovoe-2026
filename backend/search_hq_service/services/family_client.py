"""Клиент внутренней ручки user_service `/internal/family/{user_id}`.

Нужен «Я потерялся»: кого из группы звать на поиск. user_service недоступен —
семью не знаем, и тревога уходит одному краеведу: он рядом и отвечает за
группу. Ронять тревогу из-за соседнего сервиса нельзя.
"""

import logging
from urllib.parse import quote

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def family_member_ids(user_id: str) -> list[str]:
    try:
        response = httpx.get(
            f"{settings.user_service_url}/internal/family/{quote(user_id, safe='')}",
            headers={"X-Internal-Key": settings.internal_api_key},
            timeout=settings.upstream_timeout_seconds,
        )
        response.raise_for_status()
        return [str(member_id) for member_id in response.json().get("member_ids", [])]
    except (httpx.HTTPError, ValueError, AttributeError) as exc:
        logger.warning("user_service недоступен для internal/family: %s", exc)
        return []
