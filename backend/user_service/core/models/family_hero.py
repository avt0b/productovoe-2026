import enum

from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin, new_uuid


class HeroStatus(str, enum.Enum):
    """Судьба героя семейного древа — короткий статус-бейдж в UI."""

    killed_in_action = "killed_in_action"  # Погиб в бою
    missing_in_action = "missing_in_action"  # Пропал без вести
    died_of_wounds = "died_of_wounds"  # Умер от ран
    veteran = "veteran"  # Дожил до Победы / ветеран


class FamilyHero(TimestampMixin, Base):
    """Герой семейного древа — личная запись в профиле владельца.

    Не путать с ArchiveEntry(kind=soldier_card) в archive_service: там —
    публичный «народный архив» с верификацией краеведом, тут — приватная
    история семьи, которую видит только сама семья на своём/чужом профиле
    (та же «не проверяет владение», что у остальных полей Profile), а
    редактирует только владелец."""

    __tablename__ = "family_heroes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[HeroStatus] = mapped_column(
        Enum(HeroStatus, name="hero_status", native_enum=False, length=32),
        default=HeroStatus.veteran,
        nullable=False,
    )
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    death_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # «120-й стрелковый полк, Орловский рубеж» — свободный текст, не структурируем.
    unit: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    # «Подтверждено в ОБД «Мемориал»», список наград и т.п. — заметка автора,
    # не модерируется.
    note: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Необязательная связь с уже подтверждённой карточкой бойца в народном
    # архиве (archive_service, kind=soldier_card) — не валидируется, тот же
    # принцип, что squad_id у Profile.
    archive_entry_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
