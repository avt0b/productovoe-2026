from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, UUIDPrimaryKeyMixin


class RouteProgress(UUIDPrimaryKeyMixin, Base):
    """Прогресс семьи по маршруту: какие точки пройдены, где сейчас."""

    __tablename__ = "route_progress"
    __table_args__ = (UniqueConstraint("route_id", "user_id", name="uq_progress_route_user"),)

    route_id: Mapped[str] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    completed_waypoint_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    current_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
