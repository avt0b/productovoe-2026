"""Клиент внутренней ручки auth_service `/internal/users/{id}/role`.

В отличие от achievement/stats/notify-клиентов (fire-and-forget — сторонний
сервис недоступен, побочный эффект просто не случился, вызывающий метод не
роняем) здесь ошибка обязана дойти до вызывающего: это единственный шаг,
которым решение администратора по заявке реально применяется. Если
auth_service недоступен, decide() должен упасть, а не тихо оставить
пользователя без роли при approved-статусе заявки.
"""

import httpx

from core.config import settings
from core.exceptions import ServiceUnavailable


def set_role(*, user_id: str, role: str) -> None:
    try:
        response = httpx.patch(
            f"{settings.auth_service_url}/internal/users/{user_id}/role",
            headers={"X-Internal-Key": settings.internal_api_key},
            json={"role": role},
            timeout=settings.upstream_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ServiceUnavailable(f"auth_service недоступен, роль не изменена: {exc}") from exc
