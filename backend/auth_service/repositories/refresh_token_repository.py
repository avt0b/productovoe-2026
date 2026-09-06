from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import RefreshToken


class RefreshTokenRepository:
    """Доступ к таблице refresh_tokens."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, *, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        row = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(row)
        self.db.flush()
        return row

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

    def active_for_user(self, user_id: str) -> Sequence[RefreshToken]:
        return self.db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
            )
        ).all()

    def revoke(self, row: RefreshToken, *, replaced_by: str | None = None) -> None:
        row.revoked_at = datetime.now(UTC)
        row.replaced_by = replaced_by

    def revoke_all_for_user(self, user_id: str) -> None:
        now = datetime.now(UTC)
        for row in self.active_for_user(user_id):
            row.revoked_at = now
