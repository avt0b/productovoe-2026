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

# Значки ролей. Выдаёт их этот сервис — событие случается здесь.
HISTORIAN_FIRST_EXCURSION = "historian_first_excursion"  # провёл первую экскурсию
HISTORIAN_LED_GROUP = "historian_led_group"  # повёл группу по местам памяти
HISTORIAN_FIVE_STARS = "historian_five_stars"  # участник поставил пять звёзд
SEARCHER_SQUAD_FOUNDER = "searcher_squad_founder"  # завёл поисковый отряд
SEARCHER_TRIP_ORGANIZER = "searcher_trip_organizer"  # объявил выезд
SEARCHER_GOAL_REACHED = "searcher_goal_reached"  # сбор отряда собрал всю сумму


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
