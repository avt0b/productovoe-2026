from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import CurrentPrincipal, NotificationServiceDep
from api.schemas.notification import DeviceOut, DeviceRegister, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications (лента + задел под push)"])


@router.get("", response_model=list[NotificationOut])
def list_my_notifications(
    principal: CurrentPrincipal,
    service: NotificationServiceDep,
    unread_only: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[NotificationOut]:
    rows = service.for_me(principal, unread_only=unread_only, limit=limit, offset=offset)
    return [NotificationOut.model_validate(n) for n in rows]


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: str, principal: CurrentPrincipal, service: NotificationServiceDep
) -> NotificationOut:
    return NotificationOut.model_validate(service.mark_read(principal, notification_id))


@router.post("/devices", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def register_device(
    payload: DeviceRegister, principal: CurrentPrincipal, service: NotificationServiceDep
) -> DeviceOut:
    """Регистрирует токен устройства под будущую реальную push-рассылку (FCM/APNs).
    Пока только хранит токен — отправки нет, см. README сервиса."""
    device = service.register_device(principal, platform=payload.platform, token=payload.token)
    return DeviceOut.model_validate(device)


@router.delete("/devices/{token}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device(
    token: str, principal: CurrentPrincipal, service: NotificationServiceDep
) -> None:
    service.unregister_device(principal, token)
