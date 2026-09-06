from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import AdminRefreshToken


class SessionRepository:
    """Refresh-сессии админки."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(
        self,
        *,
        admin_id: str,
        token_hash: str,
        expires_at: datetime,
        ip: str = "",
        user_agent: str = "",
    ) -> AdminRefreshToken:
        row = AdminRefreshToken(
            admin_id=admin_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip=ip,
            user_agent=user_agent[:400],
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get_by_hash(self, token_hash: str) -> AdminRefreshToken | None:
        return self.db.scalar(
            select(AdminRefreshToken).where(AdminRefreshToken.token_hash == token_hash)
        )

    def list_active_for(self, admin_id: str) -> Sequence[AdminRefreshToken]:
        return self.db.scalars(
            select(AdminRefreshToken)
            .where(
                AdminRefreshToken.admin_id == admin_id,
                AdminRefreshToken.revoked_at.is_(None),
            )
            .order_by(AdminRefreshToken.created_at.desc())
        ).all()

    def revoke(self, row: AdminRefreshToken, *, replaced_by: str | None = None) -> None:
        row.revoked_at = datetime.now(UTC)
        row.replaced_by_id = replaced_by

    def revoke_all_for(self, admin_id: str) -> int:
        rows = self.list_active_for(admin_id)
        now = datetime.now(UTC)
        for row in rows:
            row.revoked_at = now
        return len(rows)
