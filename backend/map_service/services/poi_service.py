from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.db import postgis_available
from core.exceptions import NotFound, PermissionDenied
from core.geo import bbox_around, haversine_km
from core.models import POIKind, PointOfInterest
from core.security import Principal
from repositories.poi_repository import POIRepository

# Кто может дополнять слой «ВОВ» (захоронения/бои/памятники) — как и для
# «Последнего боя», рядовые посетители (family) слой не наполняют.
_CONTRIBUTOR_ROLES = {"searcher", "local_historian"}


class POIService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = POIRepository(db)

    def get(self, poi_id: str) -> PointOfInterest:
        poi = self.repo.get(poi_id)
        if poi is None:
            raise NotFound("Точка не найдена")
        return poi

    def search(self, **filters) -> Sequence[PointOfInterest]:
        return self.repo.search(**filters)

    def nearby(
        self,
        *,
        lat: float,
        lon: float,
        radius_km: float,
        kind: POIKind | None = None,
        limit: int = 100,
    ) -> list[tuple[PointOfInterest, float]]:
        if postgis_available():
            return self.repo.nearby_postgis(
                lat=lat, lon=lon, radius_km=radius_km, kind=kind, limit=limit
            )

        # Фолбэк для sqlite (тесты) и любой БД без PostGIS — см. core/geo.py.
        candidates = self.repo.search(kind=kind, bbox=bbox_around(lat, lon, radius_km), limit=1000)
        out = [(poi, haversine_km(lat, lon, poi.lat, poi.lon)) for poi in candidates]
        out = [pair for pair in out if pair[1] <= radius_km]
        out.sort(key=lambda pair: pair[1])
        return out[:limit]

    def create(self, principal: Principal, data: dict) -> PointOfInterest:
        if not (principal.is_root or principal.role in _CONTRIBUTOR_ROLES):
            raise PermissionDenied("Дополнять слой «ВОВ» могут поисковики, краеведы и наставники")
        poi = self.repo.add(PointOfInterest(created_by=principal.user_id, **data))
        self.db.commit()
        self.db.refresh(poi)
        return poi

    def update(self, principal: Principal, poi_id: str, data: dict) -> PointOfInterest:
        poi = self.get(poi_id)
        self._ensure_can_edit(principal, poi)
        for field, value in data.items():
            setattr(poi, field, value)
        self.db.commit()
        self.db.refresh(poi)
        return poi

    def delete(self, principal: Principal, poi_id: str) -> None:
        poi = self.get(poi_id)
        self._ensure_can_edit(principal, poi)
        self.repo.delete(poi)
        self.db.commit()

    @staticmethod
    def _ensure_can_edit(principal: Principal, poi: PointOfInterest) -> None:
        if principal.is_root:
            return
        if poi.created_by != principal.user_id:
            raise PermissionDenied("Редактировать точку может её автор или администратор")
