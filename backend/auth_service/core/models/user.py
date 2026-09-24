import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Role(str, enum.Enum):
    """Роль пользователя в платформе «Маршруты победы».

    Всего 4 роли по продукту: пользователь, поисковик, краевед, админ —
    последний это не значение enum, а отдельный флаг `User.is_root`."""

    family = "family"  # обычный пользователь ("пользак")
    searcher = "searcher"  # участник поискового отряда
    local_historian = "local_historian"  # краевед — только по заявке, см. historian_applications в user_service


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", native_enum=False, length=32),
        default=Role.family,
        nullable=False,
    )
    # Доступ в админку — отдельный флаг, а не роль.
    is_root: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
