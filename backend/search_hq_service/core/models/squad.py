from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Squad(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Поисковый отряд."""

    __tablename__ = "squads"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str] = mapped_column(String(120), default="", nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    contact: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    # Штаб/база отряда — чтобы потребности отряда можно было нанести на карту
    # («карта потребностей отрядов», модуль 3 ТЗ). Необязательны: не у каждого
    # отряда на момент регистрации известны точные координаты.
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    # id командира отряда (пользователь из auth_service).
    leader_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    needs: Mapped[list["SquadNeed"]] = relationship(  # noqa: F821
        back_populates="squad", cascade="all, delete-orphan"
    )
    trips: Mapped[list["VolunteerTrip"]] = relationship(  # noqa: F821
        back_populates="squad", cascade="all, delete-orphan"
    )
