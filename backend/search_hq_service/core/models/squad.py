from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Squad(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Поисковый отряд."""

    __tablename__ = "squads"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str] = mapped_column(String(120), default="", nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    contact: Mapped[str] = mapped_column(String(300), default="", nullable=False)

    # id командира отряда (пользователь из auth_service).
    leader_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    needs: Mapped[list["SquadNeed"]] = relationship(  # noqa: F821
        back_populates="squad", cascade="all, delete-orphan"
    )
    trips: Mapped[list["VolunteerTrip"]] = relationship(  # noqa: F821
        back_populates="squad", cascade="all, delete-orphan"
    )
