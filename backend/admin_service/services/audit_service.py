from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.orm import Session

from core.models import AdminUser, AuditLogEntry, AuditOutcome
from repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    def record(
        self,
        actor: AdminUser,
        *,
        action: str,
        target_service: str = "",
        target_type: str = "",
        target_id: str = "",
        target_label: str = "",
        outcome: AuditOutcome = AuditOutcome.success,
        message: str = "",
        payload: dict | None = None,
        ip: str = "",
        user_agent: str = "",
        commit: bool = True,
    ) -> AuditLogEntry:
        entry = self.repo.add(
            AuditLogEntry(
                actor_id=actor.id,
                actor_email=actor.email,
                actor_role=actor.role.value,
                action=action,
                target_service=target_service,
                target_type=target_type,
                target_id=str(target_id)[:64],
                target_label=target_label[:400],
                outcome=outcome,
                message=message[:1000],
                payload=payload or {},
                ip=ip,
                user_agent=user_agent[:400],
            )
        )
        if commit:
            self.db.commit()
            self.db.refresh(entry)
        return entry

    def search(self, **filters) -> tuple[Sequence[AuditLogEntry], int]:
        return self.repo.search(**filters)

    def recent(self, limit: int = 10) -> Sequence[AuditLogEntry]:
        return self.repo.recent(limit)

    def stats_since(self, since: datetime) -> dict:
        rows, total = self.repo.search(since=since, limit=1000)
        by_action: dict[str, int] = {}
        by_outcome = {o.value: 0 for o in AuditOutcome}
        for row in rows:
            by_action[row.action] = by_action.get(row.action, 0) + 1
            by_outcome[row.outcome.value] = by_outcome.get(row.outcome.value, 0) + 1
        return {"total": total, "by_action": by_action, "by_outcome": by_outcome}
