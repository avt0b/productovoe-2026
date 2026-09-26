from fastapi import APIRouter, Response, status

from api.deps import CurrentPrincipal, LostAlertServiceDep
from api.schemas.lost_alert import LostAlertCreate, LostAlertOut

# Без префикса: тревога поднимается на экскурсии (/excursions/{id}/lost), а
# живёт дальше сама по себе (/lost-alerts/{id}) — её открывают из уведомления,
# не зная экскурсии.
router = APIRouter(tags=["lost-alerts («Я потерялся»)"])


@router.post(
    "/excursions/{excursion_id}/lost",
    response_model=LostAlertOut,
    status_code=status.HTTP_201_CREATED,
    responses={200: {"description": "На этого человека уже есть открытая тревога — она и вернулась"}},
)
def raise_lost_alert(
    excursion_id: str,
    principal: CurrentPrincipal,
    service: LostAlertServiceDep,
    response: Response,
    payload: LostAlertCreate | None = None,
) -> LostAlertOut:
    data = payload or LostAlertCreate()
    view, created = service.raise_alert(
        principal,
        excursion_id,
        lost_user_id=data.lost_user_id,
        lat=data.lat,
        lon=data.lon,
        accuracy_m=data.accuracy_m,
        message=data.message,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return LostAlertOut.from_view(view)


# Объявлена раньше /lost-alerts/{alert_id}: иначе «active» поймался бы как id.
@router.get("/lost-alerts/active", response_model=list[LostAlertOut])
def my_active_lost_alerts(principal: CurrentPrincipal, service: LostAlertServiceDep) -> list[LostAlertOut]:
    return [LostAlertOut.from_view(view) for view in service.active_for_user(principal)]


@router.get("/lost-alerts/{alert_id}", response_model=LostAlertOut)
def get_lost_alert(alert_id: str, principal: CurrentPrincipal, service: LostAlertServiceDep) -> LostAlertOut:
    return LostAlertOut.from_view(service.get_visible(principal, alert_id))


@router.post("/lost-alerts/{alert_id}/respond", response_model=LostAlertOut)
def respond_to_lost_alert(
    alert_id: str, principal: CurrentPrincipal, service: LostAlertServiceDep
) -> LostAlertOut:
    return LostAlertOut.from_view(service.respond(principal, alert_id))


@router.post("/lost-alerts/{alert_id}/resolve", response_model=LostAlertOut)
def resolve_lost_alert(
    alert_id: str, principal: CurrentPrincipal, service: LostAlertServiceDep
) -> LostAlertOut:
    return LostAlertOut.from_view(service.resolve(principal, alert_id))


@router.post("/lost-alerts/{alert_id}/cancel", response_model=LostAlertOut)
def cancel_lost_alert(
    alert_id: str, principal: CurrentPrincipal, service: LostAlertServiceDep
) -> LostAlertOut:
    return LostAlertOut.from_view(service.cancel(principal, alert_id))
