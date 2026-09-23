import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, new_uuid


class DevicePlatform(str, enum.Enum):
    ios = "ios"
    android = "android"
    web = "web"


class Notification(Base):
    """Уведомление во внутриплатформенной ленте. Пока без реальной доставки push —
    задел под неё см. в NotificationDevice (регистрация токена под FCM)."""

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Свободная строка, не enum: список поводов будет расти (архив, экскурсии,
    # выезды...), а этот сервис не должен редеплоиться под каждый новый повод.
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationDevice(Base):
    """Токен устройства для будущей реальной push-рассылки (FCM/APNs).

    Регистрируется уже сейчас; сама отправка не реализована — это явный задел,
    подключается без изменения схемы, когда появятся Firebase-креды."""

    __tablename__ = "notification_devices"
    __table_args__ = (UniqueConstraint("token", name="uq_notification_device_token"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    platform: Mapped[DevicePlatform] = mapped_column(
        Enum(DevicePlatform, name="device_platform", native_enum=False, length=16), nullable=False
    )
    token: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
