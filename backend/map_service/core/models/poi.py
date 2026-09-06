import enum
from datetime import date

from sqlalchemy import Date, Enum, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class POIKind(str, enum.Enum):
    """Тип точки на слое «ВОВ»."""

    grave = "grave"  # воинское захоронение / братская могила
    battle = "battle"  # место боя
    monument = "monument"  # памятник / мемориал
    hospital = "hospital"  # госпиталь
    trench = "trench"  # окоп / оборонительная линия
    airfield = "airfield"  # аэродром (напр. «Нормандия — Неман»)
    other = "other"


class PointOfInterest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "points_of_interest"

    kind: Mapped[POIKind] = mapped_column(
        Enum(POIKind, name="poi_kind", native_enum=False, length=32), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)

    # Дата события: либо точная, либо человекочитаемый текст («октябрь 1941»).
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_text: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    source: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    __table_args__ = (Index("ix_poi_bbox", "lat", "lon"),)
