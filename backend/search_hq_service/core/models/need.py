import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from core.models.squad import Squad


class NeedKind(str, enum.Enum):
    volunteers = "volunteers"  # нужны люди на раскопки
    funds = "funds"  # нужны средства (ГСМ, экипировка) — целевой сбор
    equipment = "equipment"  # нужно снаряжение


class NeedStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class DonationStatus(str, enum.Enum):
    """Без платёжного шлюза донат сразу succeeded. С ЮKassa — висит pending до вебхука."""

    succeeded = "succeeded"
    pending = "pending"
    canceled = "canceled"


class SquadNeed(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Потребность отряда: «нужны 5 землекопов», «собрать 50 000 на ГСМ»."""

    __tablename__ = "squad_needs"

    squad_id: Mapped[str] = mapped_column(
        ForeignKey("squads.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[NeedKind] = mapped_column(
        Enum(NeedKind, name="need_kind", native_enum=False, length=32), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Для volunteers — сколько человек, для funds — сколько рублей.
    target_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    collected_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[NeedStatus] = mapped_column(
        Enum(NeedStatus, name="need_status", native_enum=False, length=16),
        default=NeedStatus.open,
        nullable=False,
        index=True,
    )

    squad: Mapped[Squad] = relationship(back_populates="needs")
    donations: Mapped[list["Donation"]] = relationship(
        back_populates="need", cascade="all, delete-orphan"
    )


class Donation(UUIDPrimaryKeyMixin, Base):
    """Взнос в целевой сбор (kind=funds)."""

    __tablename__ = "donations"

    need_id: Mapped[str] = mapped_column(
        ForeignKey("squad_needs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    donor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, name="donation_status", native_enum=False, length=16),
        default=DonationStatus.succeeded,
        nullable=False,
        index=True,
    )
    # id платежа в ЮKassa — только когда донат шёл через шлюз.
    payment_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    confirmation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    need: Mapped[SquadNeed] = relationship(back_populates="donations")
