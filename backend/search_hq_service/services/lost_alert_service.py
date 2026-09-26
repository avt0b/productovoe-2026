"""«Я потерялся»: участник прогулки отстал — семья из группы и краевед его ищут.

Потерявшийся жмёт «Я потерялся» (или член семьи, краевед — «Не вижу …»), и
тем, кто рядом и может помочь, приходит тревога с его точкой на карте.
Ищущие жмут «Иду», потерявшийся видит, кто к нему идёт; кто-то из них жмёт
«Нашлись» — поиск закрыт. Координаты — те же, что у прогулки: телефоны и так
присылают их каждые несколько секунд.

Фонового планировщика нет, как и у сбора с прогулкой: просроченные тревоги
закрываются при первом обращении к любой ручке тревог.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import Conflict, NotFound, PermissionDenied
from core.geo import distance_m
from core.models import (
    Excursion,
    ExcursionPosition,
    ExcursionStatus,
    LostAlert,
    LostAlertStatus,
    LostAlertWatcher,
    RegistrationStatus,
)
from core.models.lost_alert import KIND_REPORTED, KIND_SELF, RELATION_FAMILY, RELATION_GUIDE
from core.security import Principal
from core.timeutil import as_utc, utcnow
from repositories.excursion_repository import ExcursionRepository
from repositories.lost_alert_repository import LostAlertRepository
from services import family_client, notify_client, profile_client
from services.permissions import is_staff
from services.walk_service import WalkService

# Виды уведомлений — по ним приложение открывает экран поиска.
KIND_LOST_ALERT = "lost_alert"
KIND_LOST_SEARCHING = "lost_alert_searching"
KIND_LOST_RESPONDING = "lost_alert_responding"
KIND_LOST_CLOSED = "lost_alert_closed"

# Имя, если профиля нет или user_service не ответил.
FALLBACK_NAME = "Участник группы"
FALLBACK_GUIDE_NAME = "Краевед"

ROLE_LOST = "lost"
ROLE_WATCHER = "watcher"
ROLE_OBSERVER = "observer"

NOT_FOUND = "Поиск не найден"
ALREADY_CLOSED = "Поиск уже закрыт"


@dataclass(frozen=True)
class PositionView:
    lat: float
    lon: float
    accuracy_m: float | None
    updated_at: datetime


@dataclass(frozen=True)
class PersonRef:
    user_id: str
    display_name: str


@dataclass(frozen=True)
class LostPersonView:
    user_id: str
    display_name: str
    avatar_url: str | None
    is_me: bool
    position: PositionView | None


@dataclass(frozen=True)
class WatcherView:
    user_id: str
    display_name: str
    avatar_url: str | None
    relation: str
    is_me: bool
    responding: bool
    responded_at: datetime | None
    position: PositionView | None
    distance_m: int | None


@dataclass(frozen=True)
class LostAlertView:
    alert: LostAlert
    excursion_title: str
    my_role: str
    lost: LostPersonView
    raised_by: PersonRef
    watchers: list[WatcherView]
    resolved_by: PersonRef | None


class LostAlertService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = LostAlertRepository(db)
        self.excursion_repo = ExcursionRepository(db)
        self.walks = WalkService(db)

    # --- тревога ---

    def raise_alert(
        self,
        principal: Principal,
        excursion_id: str,
        *,
        lost_user_id: str | None,
        lat: float | None,
        lon: float | None,
        accuracy_m: float | None,
        message: str,
    ) -> tuple[LostAlertView, bool]:
        """Поднять тревогу. Второе значение — создана ли новая: на уже открытую
        тревогу повторное нажатие просто возвращает её, без второй рассылки."""
        self._expire_stale()
        excursion = self.walks.excursions.get(excursion_id)
        # Прогулка могла выйти по сроку, а к ней никто не обращался.
        self.walks._settle_expiry(excursion)
        if excursion.status is not ExcursionStatus.walking:
            raise Conflict("Потеряться можно только во время прогулки группы")

        is_guide = excursion.guide_id == principal.user_id or is_staff(principal)
        if not is_guide and not self._in_group(excursion, principal.user_id):
            raise PermissionDenied("Сначала отметьтесь у краеведа — встряхните телефоны рядом")

        target = lost_user_id or principal.user_id
        if target == principal.user_id:
            if is_guide:
                raise Conflict("Краевед ведёт группу — ему «Я потерялся» не нужно")
        else:
            if target == excursion.guide_id or not self._in_group(excursion, target):
                raise NotFound("Этого человека нет в группе")
            if not is_guide and target not in family_client.family_member_ids(principal.user_id):
                raise PermissionDenied("Искать можно только членов своей семьи")

        # Точка того, кто нажал, — сразу в карту группы: тревога должна
        # открыться со свежей точкой, а не ждать следующего отчёта телефона.
        if lat is not None and lon is not None:
            self.walks.record_position(
                excursion.id, principal.user_id, is_guide=is_guide,
                lat=lat, lon=lon, accuracy_m=accuracy_m,
            )

        existing = self.repo.active_for(excursion.id, target)
        if existing is not None:
            self.db.commit()
            return self._view(principal, existing, excursion), False

        now = utcnow()
        kind = KIND_SELF if target == principal.user_id else KIND_REPORTED
        alert = self.repo.add(
            LostAlert(
                excursion_id=excursion.id,
                lost_user_id=target,
                raised_by=principal.user_id,
                kind=kind,
                status=LostAlertStatus.active,
                message=message,
                created_at=now,
            )
        )
        for watcher in self._watchers_for(alert, excursion, principal, is_guide=is_guide, now=now):
            self.repo.add_watcher(watcher)
        self.db.commit()

        view = self._view(principal, alert, excursion)
        self._announce_raised(view)
        return view, True

    def active_for_user(self, principal: Principal) -> list[LostAlertView]:
        self._expire_stale()
        return [self._view(principal, alert) for alert in self.repo.active_involving(principal.user_id)]

    def get_visible(self, principal: Principal, alert_id: str) -> LostAlertView:
        alert = self._get(alert_id)
        if not self._involved(principal, alert):
            raise PermissionDenied("Этот поиск видят только семья и краевед")
        return self._view(principal, alert)

    def respond(self, principal: Principal, alert_id: str) -> LostAlertView:
        """«Иду». Потерявшемуся — одно уведомление на каждого, кто откликнулся."""
        alert = self._get(alert_id)
        watcher = self.repo.get_watcher(alert.id, principal.user_id)
        if watcher is None:
            raise PermissionDenied("Откликнуться могут только семья и краевед")
        if alert.status is not LostAlertStatus.active:
            raise Conflict(ALREADY_CLOSED)
        first_time = watcher.responded_at is None
        if first_time:
            watcher.responded_at = utcnow()
            self.db.commit()

        view = self._view(principal, alert)
        if first_time:
            name = self._watcher_name(view, principal.user_id)
            notify_client.notify_users(
                user_ids=[alert.lost_user_id],
                kind=KIND_LOST_RESPONDING,
                title=f"{name} идёт к вам",
                body=f"Оставайтесь на месте, если можете. На карте видно, где «{name}».",
                payload=self._payload(alert),
            )
        return view

    def resolve(self, principal: Principal, alert_id: str) -> LostAlertView:
        """«Нашлись». Закрыть может любой, кто в поиске: кто первым увидел, тот и жмёт."""
        alert = self._get(alert_id)
        if not self._involved(principal, alert):
            raise PermissionDenied("Закрыть поиск могут только семья, краевед и тот, кого ищут")
        if alert.status is LostAlertStatus.found:
            return self._view(principal, alert)
        if alert.status is not LostAlertStatus.active:
            raise Conflict(ALREADY_CLOSED)
        self.repo.close(alert, LostAlertStatus.found, by=principal.user_id, at=utcnow())
        self.db.commit()

        view = self._view(principal, alert)
        self._announce_closed(
            view,
            principal,
            title="Нашлись!",
            body=f"Поиск участника «{view.lost.display_name}» закрыт — все вместе.",
        )
        return view

    def cancel(self, principal: Principal, alert_id: str) -> LostAlertView:
        """Ложная тревога. Отменить может только тот, кого ищут, или тот, кто начал
        поиск: ищущий, который человека ещё не нашёл, отбой давать не должен."""
        alert = self._get(alert_id)
        if principal.user_id not in (alert.lost_user_id, alert.raised_by) and not is_staff(principal):
            raise PermissionDenied("Отменить поиск может тот, кого ищут, или тот, кто его начал")
        if alert.status is LostAlertStatus.cancelled:
            return self._view(principal, alert)
        if alert.status is not LostAlertStatus.active:
            raise Conflict(ALREADY_CLOSED)
        self.repo.close(alert, LostAlertStatus.cancelled, by=principal.user_id, at=utcnow())
        self.db.commit()

        view = self._view(principal, alert)
        self._announce_closed(
            view,
            principal,
            title="Отбой тревоги",
            body=f"Участник «{view.lost.display_name}» не потерялся — поиск отменён.",
        )
        return view

    # --- кто в поиске ---

    def _watchers_for(
        self,
        alert: LostAlert,
        excursion: Excursion,
        principal: Principal,
        *,
        is_guide: bool,
        now: datetime,
    ) -> list[LostAlertWatcher]:
        """Краевед и члены семьи потерявшегося, которые сами в этой группе.

        Родных дома тревога не касается: помочь они не могут, а напугаются.
        Семья в приложении не связана — тревога всё равно уходит краеведу.
        """
        watchers: dict[str, LostAlertWatcher] = {}

        def add(user_id: str, relation: str) -> None:
            if user_id != alert.lost_user_id and user_id not in watchers:
                watchers[user_id] = LostAlertWatcher(alert_id=alert.id, user_id=user_id, relation=relation)

        add(excursion.guide_id, RELATION_GUIDE)
        family = set(family_client.family_member_ids(alert.lost_user_id))
        for participant in self.excursion_repo.checked_in_for(excursion.id):
            if participant.user_id in family:
                add(participant.user_id, RELATION_FAMILY)

        if alert.kind == KIND_REPORTED:
            # Кто сам поднял тревогу, тот уже ищет.
            add(principal.user_id, RELATION_GUIDE if is_guide else RELATION_FAMILY)
            watchers[principal.user_id].responded_at = now
        return list(watchers.values())

    def _in_group(self, excursion: Excursion, user_id: str) -> bool:
        """Участник группы — записан и отметился бампом, как для карты прогулки."""
        participant = self.excursion_repo.get_participant(excursion.id, user_id)
        return (
            participant is not None
            and participant.status is RegistrationStatus.registered
            and participant.checked_in_at is not None
        )

    def _involved(self, principal: Principal, alert: LostAlert) -> bool:
        return (
            principal.user_id == alert.lost_user_id
            or self.repo.get_watcher(alert.id, principal.user_id) is not None
            or is_staff(principal)
        )

    # --- срок ---

    def _get(self, alert_id: str) -> LostAlert:
        self._expire_stale()
        alert = self.repo.get(alert_id)
        if alert is None:
            raise NotFound(NOT_FOUND)
        if alert.status is LostAlertStatus.active:
            # Прогулка вышла по сроку — тревога закроется вместе с ней.
            excursion = self.excursion_repo.get(alert.excursion_id)
            if excursion is not None:
                self.walks._settle_expiry(excursion)
        return alert

    def _expire_stale(self) -> None:
        """Тревоги старше срока закрываются без уведомлений: будить людей
        сообщением «поиск закрыт по времени» незачем, экран покажет это сам."""
        now = utcnow()
        ttl = timedelta(minutes=settings.lost_alert_ttl_minutes)
        stale = [alert for alert in self.repo.all_active() if as_utc(alert.created_at) + ttl <= now]
        for alert in stale:
            self.repo.close(alert, LostAlertStatus.expired, by=None, at=now)
        if stale:
            self.db.commit()

    # --- ответ ---

    def _view(self, principal: Principal, alert: LostAlert, excursion: Excursion | None = None) -> LostAlertView:
        excursion = excursion or self.excursion_repo.get(alert.excursion_id)
        guide_id = excursion.guide_id if excursion else None
        watchers = self.repo.watchers(alert.id)
        people = [alert.lost_user_id, alert.raised_by, *(w.user_id for w in watchers)]
        if alert.resolved_by:
            people.append(alert.resolved_by)
        briefs = profile_client.profile_briefs(people)

        def name(user_id: str) -> str:
            brief = briefs.get(user_id)
            if brief and brief.display_name:
                return brief.display_name
            return FALLBACK_GUIDE_NAME if user_id == guide_id else FALLBACK_NAME

        def avatar(user_id: str) -> str | None:
            brief = briefs.get(user_id)
            return brief.avatar_url if brief else None

        # Без фильтра свежести, в отличие от карты группы: «последняя точка три
        # минуты назад» ищущему полезнее, чем ничего.
        positions = {
            row.user_id: PositionView(
                lat=row.lat, lon=row.lon, accuracy_m=row.accuracy_m, updated_at=as_utc(row.updated_at)
            )
            for row in self.db.scalars(
                select(ExcursionPosition).where(ExcursionPosition.excursion_id == alert.excursion_id)
            ).all()
        }
        lost_position = positions.get(alert.lost_user_id)

        watcher_views = []
        for watcher in watchers:
            position = positions.get(watcher.user_id)
            distance = (
                round(distance_m(position.lat, position.lon, lost_position.lat, lost_position.lon))
                if position and lost_position
                else None
            )
            watcher_views.append(
                WatcherView(
                    user_id=watcher.user_id,
                    display_name=name(watcher.user_id),
                    avatar_url=avatar(watcher.user_id),
                    relation=watcher.relation,
                    is_me=watcher.user_id == principal.user_id,
                    responding=watcher.responded_at is not None,
                    responded_at=as_utc(watcher.responded_at) if watcher.responded_at else None,
                    position=position,
                    distance_m=distance,
                )
            )
        # Кто уже идёт — первым, дальше ближние: потерявшийся видит, кого ждать.
        watcher_views.sort(
            key=lambda w: (not w.responding, w.distance_m is None, w.distance_m or 0, w.user_id)
        )

        if principal.user_id == alert.lost_user_id:
            my_role = ROLE_LOST
        elif any(w.user_id == principal.user_id for w in watchers):
            my_role = ROLE_WATCHER
        else:
            my_role = ROLE_OBSERVER

        return LostAlertView(
            alert=alert,
            excursion_title=excursion.title if excursion else "",
            my_role=my_role,
            lost=LostPersonView(
                user_id=alert.lost_user_id,
                display_name=name(alert.lost_user_id),
                avatar_url=avatar(alert.lost_user_id),
                is_me=principal.user_id == alert.lost_user_id,
                position=lost_position,
            ),
            raised_by=PersonRef(user_id=alert.raised_by, display_name=name(alert.raised_by)),
            watchers=watcher_views,
            resolved_by=(
                PersonRef(user_id=alert.resolved_by, display_name=name(alert.resolved_by))
                if alert.resolved_by
                else None
            ),
        )

    # --- уведомления ---

    @staticmethod
    def _payload(alert: LostAlert, **extra: str) -> dict:
        return {"alert_id": alert.id, "excursion_id": alert.excursion_id, **extra}

    @staticmethod
    def _watcher_name(view: LostAlertView, user_id: str) -> str:
        return next((w.display_name for w in view.watchers if w.user_id == user_id), FALLBACK_NAME)

    def _announce_raised(self, view: LostAlertView) -> None:
        alert = view.alert
        lost_name = view.lost.display_name
        recipients = [w.user_id for w in view.watchers if w.user_id != alert.raised_by]
        if alert.kind == KIND_SELF:
            title = f"Потерялся участник: {lost_name}"
            body = f"Нажмите, чтобы увидеть на карте, где сейчас «{lost_name}», и проложить маршрут."
        else:
            title = f"Ищем участника: {lost_name}"
            body = (
                f"{view.raised_by.display_name} не видит «{lost_name}» рядом. "
                "Откройте карту — там последняя известная точка."
            )
        notify_client.notify_users(
            user_ids=recipients, kind=KIND_LOST_ALERT, title=title, body=body, payload=self._payload(alert)
        )
        if alert.kind == KIND_REPORTED:
            notify_client.notify_users(
                user_ids=[alert.lost_user_id],
                kind=KIND_LOST_SEARCHING,
                title="Вас ищут",
                body=(
                    f"{view.raised_by.display_name} не видит вас рядом. "
                    "Оставайтесь на месте — к вам уже идут."
                ),
                payload=self._payload(alert),
            )

    def _announce_closed(self, view: LostAlertView, principal: Principal, *, title: str, body: str) -> None:
        alert = view.alert
        recipients = [
            user_id
            for user_id in dict.fromkeys([alert.lost_user_id, *(w.user_id for w in view.watchers)])
            if user_id != principal.user_id
        ]
        notify_client.notify_users(
            user_ids=recipients,
            kind=KIND_LOST_CLOSED,
            title=title,
            body=body,
            payload=self._payload(alert, status=alert.status.value),
        )
