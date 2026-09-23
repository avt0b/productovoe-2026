from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import Squad


class SquadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, squad_id: str) -> Squad | None:
        return self.db.get(Squad, squad_id)

    def add(self, squad: Squad) -> Squad:
        self.db.add(squad)
        self.db.flush()
        return squad

    def delete(self, squad: Squad) -> None:
        self.db.delete(squad)

    def search(
        self,
        *,
        region: str | None = None,
        q: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Squad]:
        stmt = select(Squad)
        if region:
            stmt = stmt.where(Squad.region.ilike(f"%{region}%"))
        if q:
            like = f"%{q}%"
            stmt = stmt.where(Squad.name.ilike(like) | Squad.description.ilike(like))
        if bbox:
            min_lat, min_lon, max_lat, max_lon = bbox
            stmt = stmt.where(
                Squad.lat.is_not(None),
                Squad.lon.is_not(None),
                Squad.lat.between(min_lat, max_lat),
                Squad.lon.between(min_lon, max_lon),
            )
        return self.db.scalars(
            stmt.order_by(Squad.created_at.desc()).limit(limit).offset(offset)
        ).all()
