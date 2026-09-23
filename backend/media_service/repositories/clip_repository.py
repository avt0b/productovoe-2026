from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import ClipShare, ClipStatus, MemorialClip


class ClipRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, clip_id: str) -> MemorialClip | None:
        return self.db.get(MemorialClip, clip_id)

    def add(self, clip: MemorialClip) -> MemorialClip:
        self.db.add(clip)
        self.db.flush()
        return clip

    def delete(self, clip: MemorialClip) -> None:
        self.db.delete(clip)

    def search(
        self,
        *,
        status: ClipStatus | None = None,
        submitted_by: str | None = None,
        public_only: bool = False,
        poi_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MemorialClip]:
        stmt = select(MemorialClip)
        if status is not None:
            stmt = stmt.where(MemorialClip.status == status)
        if submitted_by is not None:
            stmt = stmt.where(MemorialClip.submitted_by == submitted_by)
        if public_only:
            stmt = stmt.where(MemorialClip.is_public.is_(True))
        if poi_id is not None:
            stmt = stmt.where(MemorialClip.poi_id == poi_id)
        return self.db.scalars(
            stmt.order_by(MemorialClip.created_at.desc()).limit(limit).offset(offset)
        ).all()

    def oldest_queued(self) -> MemorialClip | None:
        return self.db.scalar(
            select(MemorialClip)
            .where(MemorialClip.status == ClipStatus.queued)
            .order_by(MemorialClip.created_at.asc())
            .limit(1)
        )

    # --- shares ---

    def add_share(self, share: ClipShare) -> ClipShare:
        self.db.add(share)
        self.db.flush()
        return share

    def shares_of(self, clip_id: str) -> Sequence[ClipShare]:
        return self.db.scalars(
            select(ClipShare)
            .where(ClipShare.clip_id == clip_id)
            .order_by(ClipShare.created_at.desc())
        ).all()
