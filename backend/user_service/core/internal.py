import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from core.config import settings
from core.security import Principal

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


def internal_actor(
    x_actor_id: Annotated[str, Header(alias="X-Actor-Id")] = "",
) -> Principal:
    """Администратор, от имени которого admin_service выполняет действие.

    Права максимальные: политику «кому что можно» держит сам admin_service
    (свои роли + аудит). Здесь важно лишь донести настоящий id актора,
    чтобы он осел в created_by / verified_by и в журнале.
    """
    return Principal(user_id=x_actor_id or "admin", role="moderator", is_root=True)


InternalActor = Annotated[Principal, Depends(internal_actor)]
