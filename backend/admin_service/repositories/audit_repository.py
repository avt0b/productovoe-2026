from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.models import AuditLogEntry, AuditOutcome


class AuditRepository:
    """Журнал действий. Только добавление и чтение — по замыслу неизменяем."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, entry: AuditLogEntry) -> AuditLogEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def search(
        self,
        *,
        actor_id: str | None = None,
        action: str | None = None,
        target_service: str | None = None,
        outcome: AuditOutcome | None = None,
        since: datetime | None = None,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[AuditLogEntry], int]:
        conditions = []
        if actor_id:
            conditions.append(AuditLogEntry.actor_id == actor_id)
        if action:
            conditions.append(AuditLogEntry.action == action)
        if target_service:
            conditions.append(AuditLogEntry.target_service == target_service)
        if outcome is not None:
            conditions.append(AuditLogEntry.outcome == outcome)
        if since is not None:
            conditions.append(AuditLogEntry.created_at >= since)
        if query:
            pattern = f"%{query.strip()}%"
            conditions.append(
                AuditLogEntry.target_label.ilike(pattern)
                | AuditLogEntry.target_id.ilike(pattern)
                | AuditLogEntry.actor_email.ilike(pattern)
            )

        total = self.db.scalar(select(func.count(AuditLogEntry.id)).where(*conditions)) or 0
        rows = self.db.scalars(
            select(AuditLogEntry)
            .where(*conditions)
            .order_by(AuditLogEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return rows, total

    def recent(self, limit: int = 10) -> Sequence[AuditLogEntry]:
        return self.db.scalars(
            select(AuditLogEntry).order_by(AuditLogEntry.created_at.desc()).limit(limit)
        ).all()
