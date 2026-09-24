"""Клиент внутренней ручки user_service `/internal/achievements/award`.

user_service недоступен — не роняем находку или правку точки: значок просто не
выдастся сейчас. Синхронный вызов — побочный эффект внутри уже синхронного
метода сервиса, как notify_nearby_subscribers.
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

# Значки ролей. Выдаёт их этот сервис — событие случается здесь.
HISTORIAN_POI_AUTHOR = "historian_poi_author"  # дополнил слой «ВОВ» своей точкой
SEARCHER_FIRST_FIND = "searcher_first_find"  # отметил место «Последнего боя»
SEARCHER_ARCHIVE_CONFIRMED = "searcher_archive_confirmed"  # его место подтвердил архив
SEARCHER_REMAINS_RAISED = "searcher_remains_raised"  # с его места подняли останки


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
