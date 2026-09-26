from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import LostAlert, LostAlertStatus, LostAlertWatcher

# Прогулку нельзя закрыть, пока кого-то ищут: иначе телефоны перестанут
# присылать точки, и семья потеряет человека на карте в самый нужный момент.
OPEN_ALERT_BLOCKS_CLOSING = "Кто-то из группы потерялся — сначала найдите его или закройте поиск"


class LostAlertRepository:
    """Запросы к тревогам. Им пользуются и сервис тревог, и прогулка с
    экскурсией (запрет завершать, закрытие по сроку), поэтому общее живёт
    здесь, а не в сервисе: иначе сервисы импортировали бы друг друга по кругу."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, alert_id: str) -> LostAlert | None:
        return self.db.get(LostAlert, alert_id)

    def add(self, alert: LostAlert) -> LostAlert:
        self.db.add(alert)
        self.db.flush()
        return alert

    def add_watcher(self, watcher: LostAlertWatcher) -> LostAlertWatcher:
        self.db.add(watcher)
        return watcher

    def active_for(self, excursion_id: str, lost_user_id: str) -> LostAlert | None:
        return self.db.scalar(
            select(LostAlert).where(
                LostAlert.excursion_id == excursion_id,
                LostAlert.lost_user_id == lost_user_id,
                LostAlert.status == LostAlertStatus.active,
            )
        )

    def active_on_excursion(self, excursion_id: str) -> Sequence[LostAlert]:
        return self.db.scalars(
            select(LostAlert).where(
                LostAlert.excursion_id == excursion_id,
                LostAlert.status == LostAlertStatus.active,
            )
        ).all()

    def has_active(self, excursion_id: str) -> bool:
        return bool(self.active_on_excursion(excursion_id))

    def all_active(self) -> Sequence[LostAlert]:
        return self.db.scalars(
            select(LostAlert).where(LostAlert.status == LostAlertStatus.active)
        ).all()

    def active_involving(self, user_id: str) -> Sequence[LostAlert]:
        """Открытые тревоги, где человека ищут или он ищет. Новые первыми."""
        watching = select(LostAlertWatcher.alert_id).where(LostAlertWatcher.user_id == user_id)
        return self.db.scalars(
            select(LostAlert)
            .where(
                LostAlert.status == LostAlertStatus.active,
                (LostAlert.lost_user_id == user_id) | LostAlert.id.in_(watching),
            )
            .order_by(LostAlert.created_at.desc())
        ).all()

    def watchers(self, alert_id: str) -> Sequence[LostAlertWatcher]:
        return self.db.scalars(
            select(LostAlertWatcher).where(LostAlertWatcher.alert_id == alert_id)
        ).all()

    def get_watcher(self, alert_id: str, user_id: str) -> LostAlertWatcher | None:
        return self.db.get(LostAlertWatcher, (alert_id, user_id))

    @staticmethod
    def close(alert: LostAlert, status: LostAlertStatus, *, by: str | None, at: datetime) -> None:
        alert.status = status
        alert.resolved_at = at
        alert.resolved_by = by

    def expire_on_excursion(self, excursion_id: str, *, at: datetime) -> None:
        """Прогулка кончилась — её тревоги закрываются вместе с ней, без уведомлений."""
        for alert in self.active_on_excursion(excursion_id):
            self.close(alert, LostAlertStatus.expired, by=None, at=at)
