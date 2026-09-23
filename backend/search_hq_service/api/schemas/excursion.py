from dataclasses import asdict
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from core.models import ExcursionStatus, RegistrationStatus
from core.timeutil import as_utc
from services.bump_service import BumpOutcome, BumpResult
from services.excursion_service import ExcursionView, GatheringState
from services.walk_service import WalkState

Lat = Annotated[float, Field(ge=-90, le=90)]
Lon = Annotated[float, Field(ge=-180, le=180)]
# Точность GPS, которую сообщает телефон, в метрах.
AccuracyM = Annotated[float | None, Field(default=None, ge=0, le=10_000)]
# Все даты наружу — с поясом UTC, чтобы клиент не гадал, чьё это время.
UtcDatetime = Annotated[datetime, AfterValidator(as_utc)]


class ExcursionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    place_name: str = Field(default="", max_length=255)
    lat: Lat
    lon: Lon
    poi_id: str | None = Field(default=None, max_length=36)
    starts_at: datetime
    capacity: int = Field(default=20, ge=1, le=500)


class ExcursionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    place_name: str | None = Field(default=None, max_length=255)
    lat: Lat | None = None
    lon: Lon | None = None
    poi_id: str | None = Field(default=None, max_length=36)
    starts_at: datetime | None = None
    capacity: int | None = Field(default=None, ge=1, le=500)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class ViewerOut(BaseModel):
    is_guide: bool
    registered: bool
    checked_in_at: UtcDatetime | None


class ExcursionOut(BaseModel):
    id: str
    guide_id: str
    title: str
    description: str
    place_name: str
    lat: float
    lon: float
    poi_id: str | None
    starts_at: UtcDatetime
    capacity: int
    status: ExcursionStatus
    gathering_started_at: UtcDatetime | None
    gathering_ends_at: UtcDatetime | None
    registered_count: int
    checked_in_count: int
    # Роль того, кто смотрит. None — запрос без входа.
    viewer: ViewerOut | None
    created_at: UtcDatetime

    @classmethod
    def from_view(cls, view: ExcursionView) -> "ExcursionOut":
        excursion = view.excursion
        return cls(
            id=excursion.id,
            guide_id=excursion.guide_id,
            title=excursion.title,
            description=excursion.description,
            place_name=excursion.place_name,
            lat=excursion.lat,
            lon=excursion.lon,
            poi_id=excursion.poi_id,
            starts_at=excursion.starts_at,
            capacity=excursion.capacity,
            status=excursion.status,
            gathering_started_at=excursion.gathering_started_at,
            gathering_ends_at=excursion.gathering_ends_at,
            registered_count=view.registered_count,
            checked_in_count=view.checked_in_count,
            viewer=ViewerOut(**asdict(view.viewer)) if view.viewer else None,
            created_at=excursion.created_at,
        )


class MyExcursionsOut(BaseModel):
    guiding: list[ExcursionOut]
    joined: list[ExcursionOut]


class RegistrationCreate(BaseModel):
    """Тело запроса необязательно: по умолчанию — обычная запись одного человека.
    Школа/клуб указывает organization_name и group_size — коллективная заявка
    (модуль 5 ТЗ) держится одной строкой-регистрацией на всю группу."""

    organization_name: str = Field(default="", max_length=255)
    group_size: int = Field(default=1, ge=1, le=300)


class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    excursion_id: str
    user_id: str
    organization_name: str
    group_size: int
    status: RegistrationStatus
    checked_in_at: UtcDatetime | None
    created_at: UtcDatetime


class CheckInOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    checked_in_at: UtcDatetime


class GatheringStartIn(BaseModel):
    """Где стоит краевед, когда открывает сбор."""

    lat: Lat
    lon: Lon
    accuracy_m: AccuracyM


class GatheringOut(BaseModel):
    excursion_id: str
    status: ExcursionStatus
    is_open: bool
    started_at: UtcDatetime | None
    ends_at: UtcDatetime | None
    registered_count: int
    checked_in_count: int
    # Кто пришёл — только для краеведа; участнику приходит пустой список.
    checked_in: list[CheckInOut]
    my_checked_in_at: UtcDatetime | None

    @classmethod
    def from_state(cls, state: GatheringState) -> "GatheringOut":
        excursion = state.excursion
        return cls(
            excursion_id=excursion.id,
            status=excursion.status,
            is_open=state.is_open,
            started_at=excursion.gathering_started_at,
            ends_at=excursion.gathering_ends_at,
            registered_count=state.registered_count,
            checked_in_count=state.checked_in_count,
            checked_in=[CheckInOut.model_validate(p) for p in state.checked_in],
            my_checked_in_at=state.my_checked_in_at,
        )


class BumpIn(BaseModel):
    lat: Lat
    lon: Lon
    accuracy_m: AccuracyM
    # Сколько миллисекунд назад телефон тряхнули. Время встряски считает сервер
    # по своим часам — часы телефонов расходятся на секунды.
    shaken_ms_ago: int = Field(default=0, ge=0, le=5000)


class BumpOut(BaseModel):
    # matched — совпали, играем анимацию; no_pair — пары не нашлось, трясти ещё раз;
    # already_checked_in — участник уже отмечен раньше.
    result: BumpOutcome
    matched_user_ids: list[str]
    checked_in_at: UtcDatetime | None
    checked_in_count: int

    @classmethod
    def from_result(cls, result: BumpResult) -> "BumpOut":
        return cls(**asdict(result))


class WalkLeadIn(BaseModel):
    """Куда краевед ведёт группу: памятник из слоя «ВОВ» или точка на карте."""

    lat: Lat
    lon: Lon
    name: str = Field(default="", max_length=255)
    poi_id: str | None = Field(default=None, max_length=36)


class PositionIn(BaseModel):
    """Где сейчас телефон участника или краеведа."""

    lat: Lat
    lon: Lon
    accuracy_m: AccuracyM


class DestinationOut(BaseModel):
    lat: float
    lon: float
    name: str
    poi_id: str | None


class GroupMemberOut(BaseModel):
    user_id: str
    is_guide: bool
    is_me: bool
    lat: float
    lon: float
    accuracy_m: float | None
    updated_at: UtcDatetime


class WalkOut(BaseModel):
    excursion_id: str
    status: ExcursionStatus
    is_guide: bool
    # null — группа ещё не выходила.
    destination: DestinationOut | None
    started_at: UtcDatetime | None
    # Краевед — первым; точки старше пары минут не приходят.
    members: list[GroupMemberOut]

    @classmethod
    def from_state(cls, state: WalkState) -> "WalkOut":
        walk = state.walk
        return cls(
            excursion_id=state.excursion.id,
            status=state.excursion.status,
            is_guide=state.is_guide,
            destination=DestinationOut(
                lat=walk.destination_lat,
                lon=walk.destination_lon,
                name=walk.destination_name,
                poi_id=walk.destination_poi_id,
            )
            if walk
            else None,
            started_at=walk.started_at if walk else None,
            members=[GroupMemberOut(**asdict(member)) for member in state.members],
        )
