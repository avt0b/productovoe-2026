from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, UUIDPrimaryKeyMixin


class GuideRating(UUIDPrimaryKeyMixin, Base):
    """Оценка экскурсии и её краеведа участником, который реально пришёл (по чек-ину бампом)."""

    __tablename__ = "guide_ratings"
    __table_args__ = (
        UniqueConstraint("excursion_id", "rater_id", name="uq_guide_rating_rater"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_guide_rating_range"),
    )

    excursion_id: Mapped[str] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Денормализовано с excursion.guide_id — считать агрегат по гиду без джойна.
    guide_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    rater_id: Mapped[str] = mapped_column(String(36), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
