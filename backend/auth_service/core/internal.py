import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from core.config import settings

# Служебная плоскость. Сюда ходит только admin_service — по общему ключу,
# а не по пользовательскому JWT. Наружу /internal/* закрывается на reverse proxy.


def require_internal_key(
    x_internal_key: Annotated[str, Header(alias="X-Internal-Key")] = "",
) -> None:
    expected = settings.internal_api_key
    if not expected or not secrets.compare_digest(x_internal_key, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недействительный внутренний ключ",
        )


def internal_actor_id(
    x_actor_id: Annotated[str, Header(alias="X-Actor-Id")] = "",
) -> str:
    """id администратора, от имени которого admin_service выполняет действие."""
    return x_actor_id or "admin"
