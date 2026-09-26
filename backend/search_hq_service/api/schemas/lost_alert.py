from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from api.schemas.excursion import AccuracyM, UtcDatetime
from core.models import LostAlertStatus
from services.lost_alert_service import LostAlertView, PersonRef, PositionView, WatcherView


class LostAlertCreate(BaseModel):
    """Всё необязательно: пустое тело — «Я потерялся» без координат."""

    # Не передан или свой id — «Я потерялся»; чужой — «Не вижу …».
    lost_user_id: str | None = Field(default=None, max_length=36)
    # Где сейчас тот, кто нажал.
    lat: Annotated[float | None, Field(default=None, ge=-90, le=90)]
    lon: Annotated[float | None, Field(default=None, ge=-180, le=180)]
    accuracy_m: AccuracyM
    message: str = Field(default="", max_length=200)

    @field_validator("message")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def _coordinates_in_pair(self) -> "LostAlertCreate":
        if (self.lat is None) != (self.lon is None):
            raise ValueError("Координаты передаются парой: lat и lon")
        return self


class LostPositionOut(BaseModel):
    lat: float
    lon: float
    accuracy_m: float | None
    updated_at: UtcDatetime

    @classmethod
    def maybe(cls, position: PositionView | None) -> "LostPositionOut | None":
        if position is None:
            return None
        return cls(
            lat=position.lat, lon=position.lon, accuracy_m=position.accuracy_m, updated_at=position.updated_at
        )


class PersonRefOut(BaseModel):
    user_id: str
    display_name: str

    @classmethod
    def maybe(cls, person: PersonRef | None) -> "PersonRefOut | None":
        return cls(user_id=person.user_id, display_name=person.display_name) if person else None


class LostPersonOut(BaseModel):
    user_id: str
    display_name: str
    avatar_url: str | None
    is_me: bool
    # null — телефон ещё ни разу не присылал, где он.
    position: LostPositionOut | None


class LostWatcherOut(BaseModel):
    user_id: str
    display_name: str
    avatar_url: str | None
    relation: Literal["family", "guide"]
    is_me: bool
    # Нажал «Иду».
    responding: bool
    responded_at: UtcDatetime | None
    position: LostPositionOut | None
    # Метры до потерявшегося; null — чьей-то точки нет.
    distance_m: int | None

    @classmethod
    def from_view(cls, watcher: WatcherView) -> "LostWatcherOut":
        return cls(
            user_id=watcher.user_id,
            display_name=watcher.display_name,
            avatar_url=watcher.avatar_url,
            relation=watcher.relation,
            is_me=watcher.is_me,
            responding=watcher.responding,
            responded_at=watcher.responded_at,
            position=LostPositionOut.maybe(watcher.position),
            distance_m=watcher.distance_m,
        )


class LostAlertOut(BaseModel):
    id: str
    excursion_id: str
    excursion_title: str
    status: LostAlertStatus
    kind: Literal["self", "reported"]
    my_role: Literal["lost", "watcher", "observer"]
    message: str
    lost: LostPersonOut
    raised_by: PersonRefOut
    # Сначала откликнувшиеся, потом по расстоянию до потерявшегося.
    watchers: list[LostWatcherOut]
    created_at: UtcDatetime
    resolved_at: UtcDatetime | None
    resolved_by: PersonRefOut | None

    @classmethod
    def from_view(cls, view: LostAlertView) -> "LostAlertOut":
        alert = view.alert
        return cls(
            id=alert.id,
            excursion_id=alert.excursion_id,
            excursion_title=view.excursion_title,
            status=alert.status,
            kind=alert.kind,
            my_role=view.my_role,
            message=alert.message,
            lost=LostPersonOut(
                user_id=view.lost.user_id,
                display_name=view.lost.display_name,
                avatar_url=view.lost.avatar_url,
                is_me=view.lost.is_me,
                position=LostPositionOut.maybe(view.lost.position),
            ),
            raised_by=PersonRefOut(user_id=view.raised_by.user_id, display_name=view.raised_by.display_name),
            watchers=[LostWatcherOut.from_view(watcher) for watcher in view.watchers],
            created_at=alert.created_at,
            resolved_at=alert.resolved_at,
            resolved_by=PersonRefOut.maybe(view.resolved_by),
        )
