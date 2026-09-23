from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import Notification, NotificationDevice, Profile


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, notification_id: str) -> Notification | None:
        return self.db.get(Notification, notification_id)

    def add(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        return notification

    def for_user(
        self, user_id: str, *, unread_only: bool = False, limit: int = 100, offset: int = 0
    ) -> Sequence[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        return self.db.scalars(
            stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        ).all()

    def subscribed_with_home(self) -> Sequence[Profile]:
        """Подписанные на «Последний бой» с заданной домашней точкой — иначе радиус
        не от чего считать."""
        return self.db.scalars(
            select(Profile).where(
                Profile.subscribed_to_search.is_(True),
                Profile.home_lat.is_not(None),
                Profile.home_lon.is_not(None),
            )
        ).all()

    # --- устройства (задел под FCM) ---

    def get_device_by_token(self, token: str) -> NotificationDevice | None:
        return self.db.scalar(select(NotificationDevice).where(NotificationDevice.token == token))

    def devices_for_user(self, user_id: str) -> Sequence[NotificationDevice]:
        return self.db.scalars(
            select(NotificationDevice).where(NotificationDevice.user_id == user_id)
        ).all()

    def add_device(self, device: NotificationDevice) -> NotificationDevice:
        self.db.add(device)
        self.db.flush()
        return device

    def delete_device(self, device: NotificationDevice) -> None:
        self.db.delete(device)
