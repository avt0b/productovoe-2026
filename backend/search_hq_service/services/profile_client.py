"""Имена и аватарки людей из user_service (`GET /profiles/batch`, публичная).

Сервис хранит только id: имя человека живёт в его профиле. user_service
недоступен — отдаём пусто, и вызывающий подставляет запасное имя («Участник
группы», «Краевед»): экран поиска без имён лучше, чем экран с ошибкой.
"""

import logging
from collections.abc import Iterable
from dataclasses import dataclass

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

# Столько id принимает /profiles/batch за раз.
BATCH_LIMIT = 200


@dataclass(frozen=True)
class ProfileBrief:
    # Пустая строка — человек не заполнил имя.
    display_name: str
    avatar_url: str | None
    city: str
    role: str
    is_verified: bool


def profile_briefs(user_ids: Iterable[str]) -> dict[str, ProfileBrief]:
    """Профили по id. Кого нет в user_service — нет и в словаре."""
    wanted = list(dict.fromkeys(user_id for user_id in user_ids if user_id))
    found: dict[str, ProfileBrief] = {}
    for start in range(0, len(wanted), BATCH_LIMIT):
        chunk = wanted[start : start + BATCH_LIMIT]
        try:
            response = httpx.get(
                f"{settings.user_service_url}/profiles/batch",
                params={"ids": ",".join(chunk)},
                timeout=settings.upstream_timeout_seconds,
            )
            response.raise_for_status()
            for card in response.json():
                found[card["id"]] = ProfileBrief(
                    display_name=(card.get("display_name") or "").strip(),
                    avatar_url=card.get("avatar_url"),
                    city=card.get("city") or "",
                    role=card.get("role") or "",
                    is_verified=bool(card.get("is_verified")),
                )
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            logger.warning("user_service недоступен для profiles/batch: %s", exc)
            return {}
    return found
