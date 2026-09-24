from collections.abc import Sequence

from sqlalchemy import select, text
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
        created_by: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[LastStandPoint]:
        stmt = select(LastStandPoint)
        if status is not None:
            stmt = stmt.where(LastStandPoint.status == status)
        if created_by is not None:
            stmt = stmt.where(LastStandPoint.created_by == created_by)
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

    def nearby_postgis(
        self, *, lat: float, lon: float, radius_km: float, limit: int = 100
    ) -> list[tuple[LastStandPoint, float]]:
        """Радиус через индексированный geography-столбец (см. core/db._ensure_postgis).
        Быстрее и точнее bbox+haversine, но требует Postgres — см. LastStandService.nearby."""
        rows = self.db.execute(
            text(
                "SELECT id, "
                "ST_Distance(geog, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) "
                "/ 1000.0 AS distance_km "
                "FROM last_stand_points "
                "WHERE ST_DWithin("
                "  geog, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_m"
                ") "
                "ORDER BY geog <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography "
                "LIMIT :limit"
            ),
            {"lat": lat, "lon": lon, "radius_m": radius_km * 1000, "limit": limit},
        ).all()
        if not rows:
            return []

        by_id = {
            p.id: p
            for p in self.db.scalars(
                select(LastStandPoint).where(LastStandPoint.id.in_([row.id for row in rows]))
            )
        }
        return [(by_id[row.id], row.distance_km) for row in rows if row.id in by_id]
