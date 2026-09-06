from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import LastStandPoint, LastStandStatus


class LastStandRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, point_id: str) -> LastStandPoint | None:
        return self.db.get(LastStandPoint, point_id)

    def add(self, point: LastStandPoint) -> LastStandPoint:
        self.db.add(point)
        self.db.flush()
        return point

    def delete(self, point: LastStandPoint) -> None:
        self.db.delete(point)

    def search(
        self,
        *,
        status: LastStandStatus | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        q: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[LastStandPoint]:
        stmt = select(LastStandPoint)
        if status is not None:
            stmt = stmt.where(LastStandPoint.status == status)
        if bbox is not None:
            min_lat, min_lon, max_lat, max_lon = bbox
            stmt = stmt.where(
                LastStandPoint.lat.between(min_lat, max_lat),
                LastStandPoint.lon.between(min_lon, max_lon),
            )
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                LastStandPoint.soldier_name.ilike(like)
                | LastStandPoint.unit.ilike(like)
                | LastStandPoint.circumstances.ilike(like)
            )
        stmt = stmt.order_by(LastStandPoint.created_at.desc()).limit(limit).offset(offset)
        return self.db.scalars(stmt).all()
