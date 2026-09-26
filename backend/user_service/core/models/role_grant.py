from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin, new_uuid


class RoleGrant(TimestampMixin, Base):
    """Журнал ролей, выданных NFC-меткой (POST /role-grants/redeem).

    Метка работает без администратора, поэтому след остаётся здесь: кто
    приложил, кем был и кем стал. По журналу роли можно вернуть после показа.
    Повторное прикладывание тоже пишется — с previous_role, равной role."""

    __tablename__ = "role_grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # Ник, который прислало приложение, — только для журнала: искать по нему
    # нельзя, ники не уникальны.
    nickname: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_role: Mapped[str] = mapped_column(String(32), nullable=False)
    # Начало хэша ключа: какой меткой выдано, без самого ключа.
    key_fingerprint: Mapped[str] = mapped_column(String(12), nullable=False)
