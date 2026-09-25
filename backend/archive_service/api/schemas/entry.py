from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.models import EntryKind, EntryStatus
from core.public_url import PublicUrl

Lat = Annotated[float, Field(ge=-90, le=90)]
Lon = Annotated[float, Field(ge=-180, le=180)]


class EntryCreate(BaseModel):
    kind: EntryKind
    title: str = Field(min_length=1, max_length=255)
    body: str = ""
    lat: Lat | None = None
    lon: Lon | None = None
    event_date: date | None = None
    date_text: str = Field(default="", max_length=120)
    # Фото (имя поля историческое) и аудиовоспоминание — оба загружаются через
    # media_service POST /uploads, сюда приходят готовые ссылки.
    media_url: str | None = Field(default=None, max_length=500)
    audio_url: str | None = Field(default=None, max_length=500)
    # Точка «Последнего боя» (map_service), к которой относится запись.
    point_id: str | None = Field(default=None, max_length=36)
    # Точка слоя «ВОВ» (map_service), к которой относится запись.
    poi_id: str | None = Field(default=None, max_length=36)

    @model_validator(mode="after")
    def _coords_together(self):
        if (self.lat is None) != (self.lon is None):
            raise ValueError("lat и lon указываются вместе")
        return self


class EntryUpdate(BaseModel):
    kind: EntryKind | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = None
    lat: Lat | None = None
    lon: Lon | None = None
    event_date: date | None = None
    date_text: str | None = Field(default=None, max_length=120)
    media_url: str | None = Field(default=None, max_length=500)
    audio_url: str | None = Field(default=None, max_length=500)
    point_id: str | None = Field(default=None, max_length=36)
    poi_id: str | None = Field(default=None, max_length=36)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class ReviewRequest(BaseModel):
    note: str = Field(default="", max_length=1000)


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: EntryKind
    title: str
    body: str
    lat: float | None
    lon: float | None
    point_id: str | None
    poi_id: str | None
    event_date: date | None
    date_text: str
    media_url: PublicUrl | None
    audio_url: PublicUrl | None
    submitted_by: str
    status: EntryStatus
    verified_by: str | None
    reviewed_at: datetime | None
    review_note: str
    created_at: datetime


class EntryNearbyOut(BaseModel):
    """Минимальная витрина неподтверждённой записи рядом с точкой — для подсказки
    «помочь проверить» в семейном навигаторе. Без body и submitted_by."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: EntryKind
    title: str
    lat: float | None
    lon: float | None
    created_at: datetime


class EntryPublicOut(BaseModel):
    """Как EntryOut, но без служебной заметки модератора (review_note) —
    она не предназначена для посторонних глаз."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: EntryKind
    title: str
    body: str
    lat: float | None
    lon: float | None
    point_id: str | None
    poi_id: str | None
    event_date: date | None
    date_text: str
    media_url: PublicUrl | None
    audio_url: PublicUrl | None
    submitted_by: str
    status: EntryStatus
    verified_by: str | None
    reviewed_at: datetime | None
    created_at: datetime


class EntrySummaryOut(BaseModel):
    """Шапка раздела архива (Книга памяти): считает сервер, а не браузер —
    карточек бойцов десятки тысяч, целиком их на страницу не выгрузить."""

    total: int
    with_date: int
    on_map: int
    # Буквы, с которых начинаются заголовки, — по порядку русского алфавита.
    letters: list[str]
