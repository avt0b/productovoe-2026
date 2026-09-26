"""«Я потерялся»: участник прогулки отстал от группы — семья и краевед его ищут.

Тревога живёт отдельно от прогулки, но только внутри неё: координаты людей
берутся из тех же `excursion_positions`, куда телефоны пишут, пока группа
идёт. Кого звать на поиск, фиксируется в момент тревоги (`LostAlertWatcher`):
экран поиска опрашивает сервис каждые несколько секунд, и спрашивать
user_service про семью на каждый опрос нельзя.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, UUIDPrimaryKeyMixin, utcnow

# Вид тревоги — строкой, а не enum: член enum с именем `self` не заведёшь, а
# SQLAlchemy кладёт в колонку имя члена, не значение.
KIND_SELF = "self"  # сам нажал «Я потерялся»
KIND_REPORTED = "reported"  # член семьи или краевед нажал «Не вижу …»

# Кем ищущий приходится потерявшемуся.
RELATION_FAMILY = "family"
RELATION_GUIDE = "guide"


class LostAlertStatus(str, enum.Enum):
    active = "active"  # ищут
    found = "found"  # нашлись
    cancelled = "cancelled"  # ложная тревога
    expired = "expired"  # никто не закрыл — закрылась по сроку или вместе с прогулкой


class LostAlert(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "lost_alerts"

    excursion_id: Mapped[str] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Кого ищут.
    lost_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    # Кто поднял тревогу: сам потерявшийся, член его семьи или краевед.
    raised_by: Mapped[str] = mapped_column(String(36), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[LostAlertStatus] = mapped_column(
        Enum(LostAlertStatus, name="lost_alert_status", native_enum=False, length=16),
        default=LostAlertStatus.active,
        nullable=False,
        index=True,
    )
    # Подпись потерявшегося: «Я у фонтана».
    message: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Кто нажал «Нашлись» или «Отбой»; у закрытой по сроку — никто.
    resolved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class LostAlertWatcher(Base):
    """Кому пришла тревога: краевед и члены семьи из той же группы."""

    __tablename__ = "lost_alert_watchers"

    alert_id: Mapped[str] = mapped_column(
        ForeignKey("lost_alerts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    relation: Mapped[str] = mapped_column(String(16), nullable=False)
    # Нажал «Иду». Тот, кто сам поднял тревогу через «Не вижу …», идёт сразу.
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
