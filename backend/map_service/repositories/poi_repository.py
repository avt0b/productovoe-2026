from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import POIKind, PointOfInterest


class POIRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, poi_id: str) -> PointOfInterest | None:
        return self.db.get(PointOfInterest, poi_id)

    def add(self, poi: PointOfInterest) -> PointOfInterest:
        self.db.add(poi)
        self.db.flush()
        return poi

    def delete(self, poi: PointOfInterest) -> None:
        self.db.delete(poi)

    def search(
        self,
        *,
        kind: POIKind | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        q: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[PointOfInterest]:
        stmt = select(PointOfInterest)
        if kind is not None:
            stmt = stmt.where(PointOfInterest.kind == kind)
        if bbox is not None:
            min_lat, min_lon, max_lat, max_lon = bbox
            stmt = stmt.where(
                PointOfInterest.lat.between(min_lat, max_lat),
                PointOfInterest.lon.between(min_lon, max_lon),
            )
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                PointOfInterest.title.ilike(like) | PointOfInterest.description.ilike(like)
            )
        stmt = stmt.order_by(PointOfInterest.created_at.desc()).limit(limit).offset(offset)
        return self.db.scalars(stmt).all()
