from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin, new_uuid


class FamilyLinkInvite(TimestampMixin, Base):
    """Код приглашения в семью — один код на одно использование.

    Не путать с FamilyHero (семейное древо погибших, приватные записи
    владельца) — это про живых пользователей платформы, которые хотят
    находить друг друга (родитель/ребёнок и т.п.)."""

    __tablename__ = "family_link_invites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    inviter_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FamilyLink(TimestampMixin, Base):
    """Связь «owner_id — у него в семье member_id». Симметричная: при
    редиме инвайта создаётся по строке в каждую сторону — так `list_mine`
    не превращается в OR-запрос по двум колонкам."""

    __tablename__ = "family_links"
    __table_args__ = (UniqueConstraint("owner_id", "member_id", name="uq_family_link_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    member_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
