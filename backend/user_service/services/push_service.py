"""Доставка push по уже созданному Notification (см. services/fcm_client.py).

Вызывается после того, как уведомление создано (и, как правило, закоммичено)
— доставка push не должна срывать создание записи в ленте: если FCM
недоступен, лента всё равно работает, push просто не придёт.
"""

import logging

from sqlalchemy.orm import Session

from core.models import Notification
from repositories.notification_repository import NotificationRepository
from services import fcm_client

logger = logging.getLogger(__name__)


def deliver(db: Session, notification: Notification) -> None:
    if not fcm_client.is_configured():
        return

    repo = NotificationRepository(db)
    devices = repo.devices_for_user(notification.user_id)
    if not devices:
        return

    removed_stale = False
    for device in devices:
        result = fcm_client.send(
            token=device.token,
            title=notification.title,
            body=notification.body,
            data={"kind": notification.kind, "notification_id": notification.id},
        )
        if result is fcm_client.SendResult.token_invalid:
            logger.info("устройство %s больше не существует в FCM, удаляю", device.id)
            repo.delete_device(device)
            removed_stale = True

    if removed_stale:
        db.commit()
