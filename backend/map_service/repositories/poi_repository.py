from collections.abc import Sequence

from sqlalchemy import select, text
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

    def nearby_postgis(
        self,
        *,
        lat: float,
        lon: float,
        radius_km: float,
        kind: POIKind | None = None,
        limit: int = 100,
    ) -> list[tuple[PointOfInterest, float]]:
        """Радиус через индексированный geography-столбец (см. core/db._ensure_postgis).
        Быстрее и точнее bbox+haversine, но требует Postgres — см. POIService.nearby."""
        kind_filter = "AND kind = :kind" if kind is not None else ""
        params: dict = {"lat": lat, "lon": lon, "radius_m": radius_km * 1000, "limit": limit}
        if kind is not None:
            params["kind"] = kind.value

        rows = self.db.execute(
            text(
                "SELECT id, "
                "ST_Distance(geog, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) "
                "/ 1000.0 AS distance_km "
                "FROM points_of_interest "
                "WHERE ST_DWithin("
                "  geog, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_m"
                f") {kind_filter} "
                "ORDER BY geog <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography "
                "LIMIT :limit"
            ),
            params,
        ).all()
        if not rows:
            return []

        by_id = {
            poi.id: poi
            for poi in self.db.scalars(
                select(PointOfInterest).where(PointOfInterest.id.in_([row.id for row in rows]))
            )
        }
        return [(by_id[row.id], row.distance_km) for row in rows if row.id in by_id]
