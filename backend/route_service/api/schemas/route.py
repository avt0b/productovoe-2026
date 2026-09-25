from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field

from core.models import RouteMode
from core.public_url import PublicUrl

Lat = Annotated[float, Field(ge=-90, le=90)]
Lon = Annotated[float, Field(ge=-180, le=180)]


class RouteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    mode: RouteMode = RouteMode.family
    city: str = Field(default="", max_length=120)
    distance_km: float = Field(default=0.0, ge=0, le=100)
    cover_url: str | None = Field(default=None, max_length=500)


class RouteAutoGenerateRequest(BaseModel):
    """Автосборка черновика маршрута из точек слоя «ВОВ» рядом с (lat, lon)
    (модуль 2 ТЗ, «автоматически строить квест-маршруты»). Результат — черновик
    (`is_published=false`): контент под задания/аудио/AR всё равно нужно
    прописать вручную, автогенерация только расставляет точки на карте."""

    lat: Lat
    lon: Lon
    radius_km: float = Field(default=3.0, gt=0, le=50)
    max_points: int = Field(default=4, ge=2, le=20)
    kind: str | None = None
    title: str | None = Field(default=None, max_length=255)
    mode: RouteMode = RouteMode.family
    city: str = Field(default="", max_length=120)


class RouteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    mode: RouteMode | None = None
    city: str | None = Field(default=None, max_length=120)
    distance_km: float | None = Field(default=None, ge=0, le=100)
    cover_url: str | None = Field(default=None, max_length=500)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class WaypointCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    lat: Lat
    lon: Lon
    poi_id: str | None = Field(default=None, max_length=36)
    story: str = ""
    kid_task: str = ""
    audio_url: str | None = Field(default=None, max_length=500)
    ar_hint: str = ""
    expected_answer: str = Field(default="", max_length=255)
    order_index: int | None = Field(default=None, ge=0)


class WaypointUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    lat: Lat | None = None
    lon: Lon | None = None
    poi_id: str | None = Field(default=None, max_length=36)
    story: str | None = None
    kid_task: str | None = None
    audio_url: str | None = Field(default=None, max_length=500)
    ar_hint: str | None = None
    expected_answer: str | None = Field(default=None, max_length=255)
    order_index: int | None = Field(default=None, ge=0)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class WaypointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    route_id: str
    order_index: int
    title: str
    lat: float
    lon: float
    poi_id: str | None
    story: str
    kid_task: str
    audio_url: PublicUrl | None
    ar_hint: str
    # Эталонный ответ не отдаём наружу (спойлер загадки) — только признак,
    # что задание проверяемое, чтобы клиент показал поле ввода ответа.
    expected_answer: str = Field(default="", exclude=True, repr=False)

    @computed_field
    @property
    def has_answer(self) -> bool:
        return bool(self.expected_answer)


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    mode: RouteMode
    city: str
    distance_km: float
    cover_url: PublicUrl | None
    created_by: str
    is_published: bool
    created_at: datetime


class RouteDetailOut(RouteOut):
    waypoints: list[WaypointOut] = []


class ReorderRequest(BaseModel):
    ordered_ids: list[str] = Field(min_length=1)


class PublishRequest(BaseModel):
    is_published: bool = True


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: str
    user_id: str
    completed_waypoint_ids: list[str]
    current_index: int
    # waypoint_id -> правильно ли ответили (только точки с проверяемым заданием).
    answers: dict[str, bool]
    started_at: datetime
    completed_at: datetime | None


class CompleteWaypointRequest(BaseModel):
    waypoint_id: str
    # Ответ на kid_task, если у точки есть expected_answer. Неверный ответ
    # не блокирует прохождение — просто не засчитывается как решённый.
    answer: str | None = Field(default=None, max_length=255)


class ArchivePromptOut(BaseModel):
    """«Рядом с этой точкой есть неподтверждённая заметка — помоги проверить»."""

    waypoint_id: str
    entry_id: str
    kind: str
    title: str
    distance_km: float


class MediaPromptOut(BaseModel):
    """«У этой точки нет живого фото — предложить оживить фото бойца»."""

    waypoint_id: str
    poi_id: str
    title: str
