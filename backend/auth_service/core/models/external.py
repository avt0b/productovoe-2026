import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, UUIDPrimaryKeyMixin


class ExternalProvider(str, enum.Enum):
    """Внешний способ входа."""

    vk = "vk"  # VK ID
    yandex = "yandex"  # Яндекс ID
    max = "max"  # мессенджер MAX — через бота
    gosuslugi = "gosuslugi"  # Госуслуги (ЕСИА)


class ExternalIdentity(UUIDPrimaryKeyMixin, Base):
    """Аккаунт человека у внешнего провайдера, привязанный к нашему пользователю."""

    __tablename__ = "external_identities"
    __table_args__ = (UniqueConstraint("provider", "subject", name="uq_external_identity"),)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[ExternalProvider] = mapped_column(
        Enum(ExternalProvider, name="external_provider", native_enum=False, length=16),
        nullable=False,
    )
    # id человека у провайдера: user_id в VK ID, id в Яндекс ID, id пользователя MAX, oid в ЕСИА.
    subject: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # Почта от провайдера — только для справки. К существующему аккаунту по ней
    # не привязываем: иначе чужой аккаунт с той же почтой можно было бы угнать.
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExternalLoginStatus(str, enum.Enum):
    pending = "pending"  # ждём, пока человек подтвердит вход у провайдера
    completed = "completed"  # провайдер подтвердил — приложение может забрать токены
    consumed = "consumed"  # токены выданы, второй раз не выдаются
    failed = "failed"  # человек отказался или провайдер ответил ошибкой


class ExternalLogin(UUIDPrimaryKeyMixin, Base):
    """Одна попытка входа через внешнего провайдера. Живёт минуты."""

    __tablename__ = "external_logins"

    provider: Mapped[ExternalProvider] = mapped_column(
        Enum(ExternalProvider, name="external_provider", native_enum=False, length=16),
        nullable=False,
    )
    # Секрет попытки знает только приложение, которое начало вход. В базе — хэш:
    # утечка базы не даёт забрать чужие токены.
    login_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    # state для OAuth (VK ID, ЕСИА) или payload стартовой ссылки бота MAX.
    state: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    # PKCE: провайдер сверит его с code_challenge из ссылки входа.
    code_verifier: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    # Куда вернуть человека после подтверждения — адрес приложения.
    return_to: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    # Хэш одноразового кода, который редирект провайдера доставляет на то устройство,
    # где человек подтвердил вход. Без него токены не выдаются — даже тому, у кого login_id.
    result_code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[ExternalLoginStatus] = mapped_column(
        Enum(ExternalLoginStatus, name="external_login_status", native_enum=False, length=16),
        default=ExternalLoginStatus.pending,
        nullable=False,
    )
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_new_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Имя от провайдера — подсказка приложению для профиля: в auth_service имён нет.
    display_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    error: Mapped[str] = mapped_column(Text, default="", nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
