from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.admin_user import AdminUser
from core.models.base import Base, UUIDPrimaryKeyMixin


class AdminRefreshToken(UUIDPrimaryKeyMixin, Base):
    """Refresh-сессия админки. В БД только SHA-256 хэш самого токена.

    Ротация с детекцией повторного использования: если предъявлен уже
    отозванный токен — считаем цепочку скомпрометированной и гасим все сессии.
    """

    __tablename__ = "admin_refresh_tokens"

    admin_id: Mapped[str] = mapped_column(
        ForeignKey("admin_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    ip: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    user_agent: Mapped[str] = mapped_column(String(400), default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    admin: Mapped[AdminUser] = relationship(back_populates="sessions")

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        expires_at = self.expires_at
        if expires_at.tzinfo is None:  # sqlite отдаёт наивный datetime
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at > datetime.now(UTC)
