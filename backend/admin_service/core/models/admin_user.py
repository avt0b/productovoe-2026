import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdminRole(str, enum.Enum):
    """Роль внутри админ-панели. Не путать с ролями пользователей платформы."""

    superadmin = "superadmin"  # всё + управление учётками администраторов
    admin = "admin"  # операции над пользователями и контентом
    moderator = "moderator"  # только модерация контента
    viewer = "viewer"  # только чтение: дашборд, списки, журнал


# Кто имеет право менять данные платформы (а не только смотреть).
WRITE_ROLES = {AdminRole.superadmin, AdminRole.admin, AdminRole.moderator}


class AdminUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Учётная запись администратора. Отдельная от `users` в auth_service:
    компрометация админки не должна давать доступ к публичному API и наоборот.
    """

    __tablename__ = "admin_users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)

    role: Mapped[AdminRole] = mapped_column(
        Enum(AdminRole, name="admin_role", native_enum=False, length=32),
        default=AdminRole.viewer,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- TOTP (RFC 6238) ---
    # Секрет пишется на этапе setup и становится «боевым» только после confirm.
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- защита от перебора пароля ---
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str] = mapped_column(String(64), default="", nullable=False)

    sessions: Mapped[list["AdminRefreshToken"]] = relationship(  # noqa: F821
        back_populates="admin", cascade="all, delete-orphan"
    )
    recovery_codes: Mapped[list["RecoveryCode"]] = relationship(
        back_populates="admin", cascade="all, delete-orphan"
    )


class RecoveryCode(UUIDPrimaryKeyMixin, Base):
    """Одноразовый код восстановления на случай потери телефона с TOTP.

    Хранится только хэш — показать код можно ровно один раз, при генерации.
    """

    __tablename__ = "admin_recovery_codes"

    admin_id: Mapped[str] = mapped_column(
        ForeignKey("admin_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    admin: Mapped[AdminUser] = relationship(back_populates="recovery_codes")

    @property
    def is_used(self) -> bool:
        return self.used_at is not None
