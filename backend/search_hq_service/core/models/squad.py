import enum

from sqlalchemy import Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SquadKind(str, enum.Enum):
    """Кто стоит за «отрядом»: у музея и школьного клуба те же выезды и сборы."""

    squad = "squad"  # поисковый отряд
    museum = "museum"  # музей
    school = "school"  # школа, поисковый или краеведческий клуб


class Squad(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Поисковый отряд, музей или школа — организация, к которой человек себя относит."""

    __tablename__ = "squads"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[SquadKind] = mapped_column(
        Enum(SquadKind, name="squad_kind", native_enum=False, length=16),
        default=SquadKind.squad,
        nullable=False,
        index=True,
    )
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
