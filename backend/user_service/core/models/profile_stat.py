from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, new_uuid

# Как и код ачивки — свободная строка, не Enum в БД: новую метрику заводит
# сервис-источник события, user_service под это не редеплоится. Названия,
# которые сейчас реально шлют сервисы-источники (см. ProfileOut):
# routes_completed (route_service), excursions_completed (search_hq_service),
# finds_count (map_service + archive_service — обе точки «Последнего боя»
# и подтверждённые записи народного архива считаются одной находкой).


class ProfileStat(Base):
    __tablename__ = "profile_stats"
    __table_args__ = (UniqueConstraint("user_id", "metric", name="uq_profile_stat_user_metric"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
