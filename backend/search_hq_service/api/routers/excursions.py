from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import StreamingResponse

from api.chat_stream import chat_stream
from api.deps import (
    BumpServiceDep,
    ChatServiceDep,
    CurrentPrincipal,
    ExcursionServiceDep,
    OptionalPrincipal,
    RatingServiceDep,
    WalkServiceDep,
)
from api.schemas.chat import ChatMessageCreate, ChatMessageOut
from api.schemas.excursion import (
    BumpIn,
    BumpOut,
    ExcursionCreate,
    ExcursionOut,
    ExcursionUpdate,
    GatheringOut,
    GatheringStartIn,
    MyExcursionsOut,
    ParticipantOut,
    PositionIn,
    RegistrationCreate,
    WalkLeadIn,
    WalkOut,
)
from api.schemas.rating import GuideRatingCreate, GuideRatingOut
from core.models import ChatSubjectType

router = APIRouter(prefix="/excursions", tags=["excursions (экскурсии краеведов и бамп)"])


@router.get("", response_model=list[ExcursionOut])
def list_excursions(
    service: ExcursionServiceDep,
    principal: OptionalPrincipal,
    upcoming_only: Annotated[bool, Query()] = True,
    # Экскурсии одного краеведа — для его карточки в рейтинге.
    guide_id: Annotated[str | None, Query(max_length=36)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ExcursionOut]:
    views = service.search(
        principal, upcoming_only=upcoming_only, guide_id=guide_id, limit=limit, offset=offset
    )
    return [ExcursionOut.from_view(view) for view in views]


@router.get("/mine", response_model=MyExcursionsOut)
def my_excursions(principal: CurrentPrincipal, service: ExcursionServiceDep) -> MyExcursionsOut:
    guiding, joined = service.mine(principal)
    return MyExcursionsOut(
        guiding=[ExcursionOut.from_view(view) for view in guiding],
        joined=[ExcursionOut.from_view(view) for view in joined],
    )


@router.post("", response_model=ExcursionOut, status_code=status.HTTP_201_CREATED)
def create_excursion(
    payload: ExcursionCreate, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> ExcursionOut:
    return ExcursionOut.from_view(service.create(principal, payload.model_dump()))


@router.get("/{excursion_id}", response_model=ExcursionOut)
def get_excursion(
    excursion_id: str, principal: OptionalPrincipal, service: ExcursionServiceDep
) -> ExcursionOut:
    return ExcursionOut.from_view(service.detail(principal, excursion_id))


@router.patch("/{excursion_id}", response_model=ExcursionOut)
def update_excursion(
    excursion_id: str,
    payload: ExcursionUpdate,
    principal: CurrentPrincipal,
    service: ExcursionServiceDep,
) -> ExcursionOut:
    view = service.update(principal, excursion_id, payload.to_update_dict())
    return ExcursionOut.from_view(view)


@router.post("/{excursion_id}/cancel", response_model=ExcursionOut)
def cancel_excursion(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> ExcursionOut:
    return ExcursionOut.from_view(service.cancel(principal, excursion_id))


# --- запись участников ---


@router.post(
    "/{excursion_id}/registrations",
    response_model=ParticipantOut,
    status_code=status.HTTP_201_CREATED,
)
def register_for_excursion(
    excursion_id: str,
    principal: CurrentPrincipal,
    service: ExcursionServiceDep,
    payload: RegistrationCreate | None = None,
) -> ParticipantOut:
    data = payload or RegistrationCreate()
    return ParticipantOut.model_validate(
        service.register(
            principal,
            excursion_id,
            organization_name=data.organization_name,
            group_size=data.group_size,
        )
    )


@router.delete("/{excursion_id}/registrations/me", status_code=status.HTTP_204_NO_CONTENT)
def cancel_registration(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> None:
    service.cancel_registration(principal, excursion_id)


@router.get("/{excursion_id}/participants", response_model=list[ParticipantOut])
def list_participants(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> list[ParticipantOut]:
    rows = service.participants(principal, excursion_id)
    return [ParticipantOut.model_validate(row) for row in rows]


# --- сбор группы и бамп ---


@router.post("/{excursion_id}/gathering/start", response_model=GatheringOut)
def start_gathering(
    excursion_id: str,
    payload: GatheringStartIn,
    principal: CurrentPrincipal,
    service: ExcursionServiceDep,
) -> GatheringOut:
    state = service.start_gathering(
        principal, excursion_id, lat=payload.lat, lon=payload.lon, accuracy_m=payload.accuracy_m
    )
    return GatheringOut.from_state(state)


@router.post("/{excursion_id}/gathering/finish", response_model=GatheringOut)
def finish_gathering(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> GatheringOut:
    return GatheringOut.from_state(service.finish_gathering(principal, excursion_id))


@router.get("/{excursion_id}/gathering", response_model=GatheringOut)
def gathering_state(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> GatheringOut:
    return GatheringOut.from_state(service.gathering_state(principal, excursion_id))


@router.post("/{excursion_id}/walk", response_model=WalkOut)
def lead_walk(
    excursion_id: str, payload: WalkLeadIn, principal: CurrentPrincipal, service: WalkServiceDep
) -> WalkOut:
    """Краевед ведёт группу к месту. Первый вызов закрывает сбор и зовёт отмеченных
    на карту; следующие только меняют цель."""
    state = service.lead(
        principal,
        excursion_id,
        lat=payload.lat,
        lon=payload.lon,
        name=payload.name,
        poi_id=payload.poi_id,
    )
    return WalkOut.from_state(state)


@router.get("/{excursion_id}/walk", response_model=WalkOut)
def walk_state(excursion_id: str, principal: CurrentPrincipal, service: WalkServiceDep) -> WalkOut:
    """Цель и где сейчас группа. Видят краевед и отметившиеся бампом."""
    return WalkOut.from_state(service.state(principal, excursion_id))


@router.put("/{excursion_id}/walk/position", status_code=status.HTTP_204_NO_CONTENT)
def report_position(
    excursion_id: str, payload: PositionIn, principal: CurrentPrincipal, service: WalkServiceDep
) -> None:
    service.report_position(
        principal, excursion_id, lat=payload.lat, lon=payload.lon, accuracy_m=payload.accuracy_m
    )


@router.post("/{excursion_id}/walk/finish", response_model=WalkOut)
def finish_walk(excursion_id: str, principal: CurrentPrincipal, service: WalkServiceDep) -> WalkOut:
    return WalkOut.from_state(service.finish(principal, excursion_id))


@router.post("/{excursion_id}/bumps", response_model=BumpOut)
def bump(
    excursion_id: str, payload: BumpIn, principal: CurrentPrincipal, service: BumpServiceDep
) -> BumpOut:
    # Синхронный обработчик: FastAPI держит его в пуле потоков, и ожидание пары
    # до пары секунд не блокирует остальные запросы.
    result = service.bump(
        principal,
        excursion_id,
        lat=payload.lat,
        lon=payload.lon,
        accuracy_m=payload.accuracy_m,
        shaken_ms_ago=payload.shaken_ms_ago,
    )
    return BumpOut.from_result(result)


# --- рейтинг гида ---


@router.post(
    "/{excursion_id}/rating", response_model=GuideRatingOut, status_code=status.HTTP_201_CREATED
)
def rate_excursion(
    excursion_id: str,
    payload: GuideRatingCreate,
    principal: CurrentPrincipal,
    service: RatingServiceDep,
) -> GuideRatingOut:
    rating = service.rate(principal, excursion_id, rating=payload.rating, comment=payload.comment)
    return GuideRatingOut.model_validate(rating)


@router.get("/{excursion_id}/rating", response_model=list[GuideRatingOut])
def excursion_ratings(excursion_id: str, service: RatingServiceDep) -> list[GuideRatingOut]:
    return [GuideRatingOut.model_validate(r) for r in service.for_excursion(excursion_id)]


# --- чат сбора ---


@router.get("/{excursion_id}/messages", response_model=list[ChatMessageOut])
def list_excursion_messages(
    excursion_id: str,
    principal: CurrentPrincipal,
    service: ChatServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    since: Annotated[datetime | None, Query()] = None,
) -> list[ChatMessageOut]:
    """Последние сообщения по порядку; `since` — только написанные не раньше."""
    rows = service.excursion_messages(
        principal, excursion_id, limit=limit, offset=offset, since=since
    )
    return [ChatMessageOut.model_validate(r) for r in rows]


@router.get("/{excursion_id}/messages/stream", response_class=StreamingResponse)
async def stream_excursion_messages(
    excursion_id: str, request: Request, principal: CurrentPrincipal
) -> StreamingResponse:
    """Новые сообщения чата сбора — Server-Sent Events, событие `message`."""
    return await chat_stream(request, principal, ChatSubjectType.excursion, excursion_id)


@router.post(
    "/{excursion_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED
)
def post_excursion_message(
    excursion_id: str,
    payload: ChatMessageCreate,
    principal: CurrentPrincipal,
    service: ChatServiceDep,
) -> ChatMessageOut:
    return ChatMessageOut.model_validate(
        service.post_excursion_message(principal, excursion_id, payload.body)
    )
