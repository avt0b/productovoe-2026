from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import NotFound, PermissionDenied
from core.geo import haversine_km
from core.models import DevicePlatform, Notification, NotificationDevice
from core.models.base import utcnow
from core.security import Principal
from repositories.notification_repository import NotificationRepository
from services import push_service


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NotificationRepository(db)

    # --- лента ---

    def for_me(
        self, principal: Principal, *, unread_only: bool = False, limit: int = 100, offset: int = 0
    ) -> Sequence[Notification]:
        return self.repo.for_user(
            principal.user_id, unread_only=unread_only, limit=limit, offset=offset
        )

    def mark_read(self, principal: Principal, notification_id: str) -> Notification:
        notification = self.repo.get(notification_id)
        if notification is None:
            raise NotFound("Уведомление не найдено")
        if notification.user_id != principal.user_id:
            raise PermissionDenied("Это не ваше уведомление")
        if notification.read_at is None:
            notification.read_at = utcnow()
            self.db.commit()
            self.db.refresh(notification)
        return notification

    # --- устройства (реальная push-доставка — см. services/fcm_client.py) ---

    def register_device(
        self, principal: Principal, *, platform: DevicePlatform, token: str
    ) -> NotificationDevice:
        existing = self.repo.get_device_by_token(token)
        if existing is not None:
            existing.user_id = principal.user_id
            existing.platform = platform
            self.db.commit()
            self.db.refresh(existing)
            return existing
        device = self.repo.add_device(
            NotificationDevice(user_id=principal.user_id, platform=platform, token=token)
        )
        self.db.commit()
        self.db.refresh(device)
        return device

    def unregister_device(self, principal: Principal, token: str) -> None:
        device = self.repo.get_device_by_token(token)
        if device is None or device.user_id != principal.user_id:
            raise NotFound("Устройство не найдено")
        self.repo.delete_device(device)
        self.db.commit()

    # --- рассылка (вызывается из /internal, см. api/routers/internal.py) ---

    def notify_users(
        self, *, user_ids: list[str], kind: str, title: str, body: str, payload: dict | None
    ) -> int:
        """Уведомляет конкретных людей. Возвращает число созданных уведомлений.

        Профиль для этого не нужен: уведомление привязано к user_id, а не к
        профилю, — человек, ещё не заполнивший профиль, тоже должен узнать, что
        его ждут на сборе.
        """
        # Один и тот же человек мог попасть в список дважды — второе уведомление
        # о том же событии было бы шумом.
        unique_ids = list(dict.fromkeys(user_id for user_id in user_ids if user_id))
        for user_id in unique_ids:
            notification = self.repo.add(
                Notification(user_id=user_id, kind=kind, title=title, body=body, payload=payload)
            )
            push_service.deliver(self.db, notification)
        if unique_ids:
            self.db.commit()
        return len(unique_ids)

    def broadcast_nearby(
        self, *, lat: float, lon: float, kind: str, title: str, body: str, payload: dict | None
    ) -> int:
        """Уведомляет подписчиков «Последнего боя», для которых точка попала в их
        собственный alert_radius_km от домашних координат. Возвращает число созданных
        уведомлений."""
        created = 0
        for profile in self.repo.subscribed_with_home():
            distance_km = haversine_km(lat, lon, profile.home_lat, profile.home_lon)
            if distance_km > profile.alert_radius_km:
                continue
            # title/body могут нести плейсхолдер "{distance_km}" — подставляем
            # реальное расстояние до конкретного подписчика (кейс: «в 5 км от вас»).
            distance_label = str(max(1, round(distance_km)))
            notification = self.repo.add(
                Notification(
                    user_id=profile.id,
                    kind=kind,
                    title=title.replace("{distance_km}", distance_label),
                    body=body.replace("{distance_km}", distance_label),
                    payload={**(payload or {}), "distance_km": round(distance_km, 2)},
                )
            )
            push_service.deliver(self.db, notification)
            created += 1
        if created:
            self.db.commit()
        return created
