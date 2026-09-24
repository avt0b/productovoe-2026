from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import ArchiveEntry, EntryKind, EntryStatus


class EntryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, entry_id: str) -> ArchiveEntry | None:
        return self.db.get(ArchiveEntry, entry_id)

    def add(self, entry: ArchiveEntry) -> ArchiveEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def delete(self, entry: ArchiveEntry) -> None:
        self.db.delete(entry)

    def search(
        self,
        *,
        status: EntryStatus | None = None,
        kind: EntryKind | None = None,
        submitted_by: str | None = None,
        point_id: str | None = None,
        poi_id: str | None = None,
        q: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ArchiveEntry]:
        stmt = select(ArchiveEntry)
        if status is not None:
            stmt = stmt.where(ArchiveEntry.status == status)
        if kind is not None:
            stmt = stmt.where(ArchiveEntry.kind == kind)
        if submitted_by is not None:
            stmt = stmt.where(ArchiveEntry.submitted_by == submitted_by)
        if point_id is not None:
            stmt = stmt.where(ArchiveEntry.point_id == point_id)
        if poi_id is not None:
            stmt = stmt.where(ArchiveEntry.poi_id == poi_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(ArchiveEntry.title.ilike(like) | ArchiveEntry.body.ilike(like))
        if bbox is not None:
            min_lat, min_lon, max_lat, max_lon = bbox
            stmt = stmt.where(
                ArchiveEntry.lat.is_not(None),
                ArchiveEntry.lon.is_not(None),
                ArchiveEntry.lat.between(min_lat, max_lat),
                ArchiveEntry.lon.between(min_lon, max_lon),
            )
        return self.db.scalars(
            stmt.order_by(ArchiveEntry.created_at.desc()).limit(limit).offset(offset)
        ).all()
