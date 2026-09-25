from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.db import postgis_available
from core.exceptions import NotFound, PermissionDenied
from core.geo import bbox_around, haversine_km
from core.models import LastStandPoint, LastStandStatus
from core.security import Principal
from repositories.last_stand_repository import LastStandRepository
from services import achievement_client
from services.notify_client import notify_nearby_subscribers
from services.stats_client import increment_stat

STAT_FINDS_COUNT = "finds_count"

STATUS_BADGES = {
    LastStandStatus.archive_confirmed: achievement_client.SEARCHER_ARCHIVE_CONFIRMED,
    LastStandStatus.remains_raised: achievement_client.SEARCHER_REMAINS_RAISED,
}

# Кто может заводить точки «Последнего боя».
_CONTRIBUTOR_ROLES = {"searcher", "local_historian"}


class LastStandService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = LastStandRepository(db)

    def get(self, point_id: str) -> LastStandPoint:
        point = self.repo.get(point_id)
        if point is None:
            raise NotFound("Точка не найдена")
        return point

    def search(self, **filters) -> Sequence[LastStandPoint]:
        return self.repo.search(**filters)

    def nearby(
        self, *, lat: float, lon: float, radius_km: float, limit: int = 100
    ) -> list[tuple[LastStandPoint, float]]:
        if postgis_available():
            return self.repo.nearby_postgis(lat=lat, lon=lon, radius_km=radius_km, limit=limit)

        # Фолбэк для sqlite (тесты) и любой БД без PostGIS — см. core/geo.py.
        candidates = self.repo.search(bbox=bbox_around(lat, lon, radius_km), limit=1000)
        out = [(p, haversine_km(lat, lon, p.lat, p.lon)) for p in candidates]
        out = [pair for pair in out if pair[1] <= radius_km]
        out.sort(key=lambda pair: pair[1])
        return out[:limit]

    def create(self, principal: Principal, data: dict) -> LastStandPoint:
        if not (principal.is_root or principal.role in _CONTRIBUTOR_ROLES):
            raise PermissionDenied(
                "Добавлять точки «Последнего боя» могут поисковики, краеведы и наставники"
            )
        point = self.repo.add(LastStandPoint(created_by=principal.user_id, **data))
        self.db.commit()
        self.db.refresh(point)

        # "{distance_km}" — плейсхолдер, user_service подставит реальную
        # дистанцию до конкретного подписчика (см. NotificationService.broadcast_nearby).
        title = (
            f"Обнаружено место гибели: {point.soldier_name} — в {{distance_km}} км от вас"
            if point.soldier_name
            else "В {distance_km} км от вас обнаружено место гибели бойца"
        )
        notify_nearby_subscribers(
            lat=point.lat,
            lon=point.lon,
            title=title,
            body="Требуется помощь в идентификации.",
        )
        increment_stat(user_id=principal.user_id, metric=STAT_FINDS_COUNT)
        achievement_client.award_achievement(
            user_id=principal.user_id, code=achievement_client.SEARCHER_FIRST_FIND
        )
        return point

    def update(self, principal: Principal, point_id: str, data: dict) -> LastStandPoint:
        point = self.get(point_id)
        self._ensure_can_edit(principal, point)
        for field, value in data.items():
            setattr(point, field, value)
        self.db.commit()
        self.db.refresh(point)
        return point

    def set_status(
        self, principal: Principal, point_id: str, status: LastStandStatus
    ) -> LastStandPoint:
        if not principal.is_root:
            raise PermissionDenied("Менять статус может только администратор")
        point = self.get(point_id)
        point.status = status
        self.db.commit()
        self.db.refresh(point)
        # Значок — тому, кто место нашёл, а не администратору, что сменил стадию.
        code = STATUS_BADGES.get(status)
        if code:
            achievement_client.award_achievement(user_id=point.created_by, code=code)
        return point

    def delete(self, principal: Principal, point_id: str) -> None:
        point = self.get(point_id)
        self._ensure_can_edit(principal, point)
        self.repo.delete(point)
        self.db.commit()

    @staticmethod
    def _ensure_can_edit(principal: Principal, point: LastStandPoint) -> None:
        if principal.is_root:
            return
        if point.created_by != principal.user_id:
            raise PermissionDenied("Редактировать точку может её автор или администратор")
