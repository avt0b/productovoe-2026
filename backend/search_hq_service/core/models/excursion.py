import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from core.models.trip import RegistrationStatus


class ExcursionStatus(str, enum.Enum):
    """Жизненный цикл экскурсии краеведа."""

    scheduled = "scheduled"  # заявка опубликована, идёт запись
    gathering = "gathering"  # краевед на месте, группа отмечается бампом
    walking = "walking"  # группа собрана, краевед ведёт её к памятному месту
    finished = "finished"  # сбор закрыт
    cancelled = "cancelled"  # краевед отменил экскурсию


class Excursion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Экскурсия краеведа или наставника в точке на карте."""

    __tablename__ = "excursions"

    # id краеведа (пользователь из auth_service).
    guide_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Место сбора группы: бамп засчитывается только рядом с этой точкой.
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    place_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # То же место на слое «ВОВ» в map_service, если экскурсия у памятника.
    poi_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, default=20, nullable=False)

    status: Mapped[ExcursionStatus] = mapped_column(
        Enum(ExcursionStatus, name="excursion_status", native_enum=False, length=16),
        default=ExcursionStatus.scheduled,
        nullable=False,
        index=True,
    )
    gathering_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    gathering_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    participants: Mapped[list["ExcursionParticipant"]] = relationship(
        back_populates="excursion", cascade="all, delete-orphan"
    )
    # Маршрут после сбора. selectin — точки всех экскурсий списка приходят одним
    # запросом, а не по запросу на каждую.
    stops: Mapped[list["ExcursionStop"]] = relationship(
        cascade="all, delete-orphan",
        order_by="ExcursionStop.position",
        lazy="selectin",
    )


class ExcursionStop(UUIDPrimaryKeyMixin, Base):
    """Точка маршрута экскурсии: краевед ведёт группу от места сбора по ним по порядку.

    Своя таблица, а не колонки в `excursions`: `create_all` новую таблицу на
    развёрнутой базе просто создаст, а колонку в старую не добавит.
    """

    __tablename__ = "excursion_stops"

    excursion_id: Mapped[str] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    # Та же точка на слое «ВОВ» в map_service, если её выбрали оттуда.
    poi_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # Что здесь рассказать или сделать: история места, задание группе.
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)


class ExcursionParticipant(UUIDPrimaryKeyMixin, Base):
    """Запись человека на экскурсию и отметка, что он пришёл."""

    __tablename__ = "excursion_participants"
    __table_args__ = (
        UniqueConstraint("excursion_id", "user_id", name="uq_excursion_user"),
        CheckConstraint("group_size >= 1", name="ck_participant_group_size_positive"),
    )

    excursion_id: Mapped[str] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # Коллективная заявка школы/клуба (модуль 5 ТЗ): один аккаунт-представитель
    # записывает группу целиком — задача сама по себе не заводит отдельный
    # аккаунт на каждого ученика.
    organization_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    group_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status", native_enum=False, length=16),
        default=RegistrationStatus.registered,
        nullable=False,
    )
    # Момент, когда бамп с краеведом совпал: человек реально пришёл на место.
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    excursion: Mapped[Excursion] = relationship(back_populates="participants")


class ExcursionWalk(Base):
    """Куда краевед ведёт собранную группу.

    Место сбора и памятное место — разные точки: группа собирается у выхода из
    метро, а идёт к братской могиле. Своя таблица, а не колонки в `excursions`:
    схема создаётся `create_all`, и новая колонка в существующей таблице уронила
    бы уже развёрнутую базу — новая таблица просто появится рядом.
    """

    __tablename__ = "excursion_walks"

    excursion_id: Mapped[str] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"), primary_key=True
    )
    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lon: Mapped[float] = mapped_column(Float, nullable=False)
    destination_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # Точка слоя «ВОВ» из map_service, если место выбрано из него, а не на карте.
    destination_poi_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Когда цель последний раз менялась: краевед ведёт группу от места к месту.
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExcursionPosition(Base):
    """Где сейчас человек из группы — последняя присланная точка.

    Одна строка на человека: история перемещений никому не нужна, а таблица
    не должна расти, пока группа идёт. Старые точки отсекаются при чтении.
    """

    __tablename__ = "excursion_positions"

    excursion_id: Mapped[str] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    is_guide: Mapped[bool] = mapped_column(default=False, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
