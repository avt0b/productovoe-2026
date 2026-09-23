from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import Conflict, NotFound, PermissionDenied
from core.geo import distance_m
from core.models import Excursion, ExcursionParticipant, ExcursionStatus, RegistrationStatus
from core.security import Principal
from core.timeutil import as_utc, utcnow
from repositories.excursion_repository import ExcursionRepository
from services import stats_client
from services.bump_matcher import bump_matcher
from services.permissions import can_guide, is_staff


@dataclass(frozen=True)
class ViewerState:
    """Кем экскурсия приходится тому, кто её смотрит."""

    is_guide: bool
    registered: bool
    checked_in_at: datetime | None


@dataclass(frozen=True)
class ExcursionView:
    excursion: Excursion
    registered_count: int
    checked_in_count: int
    # None — смотрят без входа.
    viewer: ViewerState | None


@dataclass(frozen=True)
class GatheringState:
    excursion: Excursion
    is_open: bool
    registered_count: int
    checked_in_count: int
    # Кто уже пришёл — видит только краевед; участнику список не отдаём.
    checked_in: Sequence[ExcursionParticipant]
    my_checked_in_at: datetime | None


class ExcursionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExcursionRepository(db)

    # --- чтение ---

    def get(self, excursion_id: str) -> Excursion:
        excursion = self.repo.get(excursion_id)
        if excursion is None:
            raise NotFound("Экскурсия не найдена")
        return excursion

    def detail(self, principal: Principal | None, excursion_id: str) -> ExcursionView:
        return self._views(principal, [self.get(excursion_id)])[0]

    def search(self, principal: Principal | None, **filters) -> list[ExcursionView]:
        return self._views(principal, self.repo.search(**filters))

    def mine(self, principal: Principal) -> tuple[list[ExcursionView], list[ExcursionView]]:
        """Экскурсии, которые человек ведёт, и те, на которые записан."""
        guiding = self.repo.search(upcoming_only=False, guide_id=principal.user_id, limit=200)
        joined = self.repo.joined_by(principal.user_id)
        return self._views(principal, guiding), self._views(principal, joined)

    # --- краевед ---

    def create(self, principal: Principal, data: dict) -> ExcursionView:
        if not can_guide(principal):
            raise PermissionDenied("Создать экскурсию может краевед, наставник или модератор")
        data["starts_at"] = as_utc(data["starts_at"])
        excursion = self.repo.add(Excursion(guide_id=principal.user_id, **data))
        self.db.commit()
        self.db.refresh(excursion)
        return self._views(principal, [excursion])[0]

    def update(self, principal: Principal, excursion_id: str, data: dict) -> ExcursionView:
        excursion = self.get(excursion_id)
        self._ensure_guide(principal, excursion)
        if excursion.status is not ExcursionStatus.scheduled:
            raise Conflict("Экскурсию можно менять, пока не начался сбор")
        if "capacity" in data and data["capacity"] < self.repo.count_registered(excursion_id):
            raise Conflict("Мест не может быть меньше, чем уже записалось")
        if data.get("starts_at") is not None:
            data["starts_at"] = as_utc(data["starts_at"])
        for field, value in data.items():
            setattr(excursion, field, value)
        self.db.commit()
        self.db.refresh(excursion)
        return self._views(principal, [excursion])[0]

    def cancel(self, principal: Principal, excursion_id: str) -> ExcursionView:
        excursion = self.get(excursion_id)
        self._ensure_guide(principal, excursion)
        if excursion.status in (ExcursionStatus.finished, ExcursionStatus.cancelled):
            raise Conflict("Экскурсия уже завершена или отменена")
        excursion.status = ExcursionStatus.cancelled
        self.db.commit()
        bump_matcher.forget(excursion_id)
        self.db.refresh(excursion)
        return self._views(principal, [excursion])[0]

    def participants(
        self, principal: Principal, excursion_id: str
    ) -> Sequence[ExcursionParticipant]:
        self._ensure_guide(principal, self.get(excursion_id))
        return self.repo.participants_for(excursion_id)

    # --- запись участников ---

    def register(
        self,
        principal: Principal,
        excursion_id: str,
        *,
        organization_name: str = "",
        group_size: int = 1,
    ) -> ExcursionParticipant:
        excursion = self.get(excursion_id)
        if excursion.guide_id == principal.user_id:
            raise Conflict("Краевед не записывается на свою экскурсию")
        # Записаться можно только заранее: пришедших без записи бамп не отмечает.
        if excursion.status is not ExcursionStatus.scheduled:
            raise Conflict("Запись закрыта: сбор уже начался или экскурсия завершена")

        existing = self.repo.get_participant(excursion_id, principal.user_id)
        already_registered = existing is not None and existing.status is RegistrationStatus.registered
        # Заявка коллективная (модуль 5 ТЗ): один представитель школы/клуба
        # держит одну строку-регистрацию на всю группу — capacity считаем по
        # сумме group_size, а не по числу строк.
        previous_size = existing.group_size if already_registered else 0
        occupied = self.repo.count_registered(excursion_id)
        projected = occupied - previous_size + group_size
        if projected > excursion.capacity:
            raise Conflict("Мест не хватит на всю группу")

        if existing:
            existing.status = RegistrationStatus.registered
            existing.organization_name = organization_name
            existing.group_size = group_size
            participant = existing
        else:
            participant = self.repo.add_participant(
                ExcursionParticipant(
                    excursion_id=excursion_id,
                    user_id=principal.user_id,
                    organization_name=organization_name,
                    group_size=group_size,
                )
            )
        self.db.commit()
        self.db.refresh(participant)
        return participant

    def cancel_registration(self, principal: Principal, excursion_id: str) -> None:
        excursion = self.get(excursion_id)
        if excursion.status is not ExcursionStatus.scheduled:
            raise Conflict("После начала сбора отписаться нельзя")
        participant = self.repo.get_participant(excursion_id, principal.user_id)
        if participant is None or participant.status is RegistrationStatus.cancelled:
            raise NotFound("Запись не найдена")
        participant.status = RegistrationStatus.cancelled
        self.db.commit()

    # --- сбор группы ---

    def start_gathering(
        self,
        principal: Principal,
        excursion_id: str,
        *,
        lat: float,
        lon: float,
        accuracy_m: float | None,
    ) -> GatheringState:
        excursion = self.get(excursion_id)
        self._ensure_guide(principal, excursion)
        self._close_if_expired(excursion)
        if excursion.status is ExcursionStatus.gathering:
            return self.gathering_state(principal, excursion_id)
        if excursion.status is not ExcursionStatus.scheduled:
            raise Conflict("Экскурсия уже завершена или отменена")
        # Краевед открывает сбор, стоя на месте: иначе группа будет трясти телефоны впустую.
        self.ensure_on_site(excursion, lat=lat, lon=lon, accuracy_m=accuracy_m)

        now = utcnow()
        excursion.status = ExcursionStatus.gathering
        excursion.gathering_started_at = now
        excursion.gathering_ends_at = now + timedelta(minutes=settings.gathering_duration_minutes)
        self.db.commit()
        return self.gathering_state(principal, excursion_id)

    def finish_gathering(self, principal: Principal, excursion_id: str) -> GatheringState:
        excursion = self.get(excursion_id)
        self._ensure_guide(principal, excursion)
        already_expired = self._close_if_expired(excursion)
        just_finished = False
        if excursion.status is ExcursionStatus.gathering:
            excursion.status = ExcursionStatus.finished
            excursion.gathering_ends_at = utcnow()
            just_finished = True
        elif excursion.status is not ExcursionStatus.finished:
            raise Conflict("Сбор группы ещё не начинался")
        self.db.commit()
        if already_expired or just_finished:
            self._credit_excursion_completion(excursion)
        bump_matcher.forget(excursion_id)
        return self.gathering_state(principal, excursion_id)

    def gathering_state(self, principal: Principal, excursion_id: str) -> GatheringState:
        excursion = self.get(excursion_id)
        if self._close_if_expired(excursion):
            self.db.commit()
            self._credit_excursion_completion(excursion)

        is_guide = excursion.guide_id == principal.user_id or is_staff(principal)
        me = self.repo.get_participant(excursion_id, principal.user_id)
        registered = me is not None and me.status is RegistrationStatus.registered
        if not is_guide and not registered:
            raise PermissionDenied("Сбор видят краевед и записавшиеся участники")

        checked_in = self.repo.checked_in_for(excursion_id)
        return GatheringState(
            excursion=excursion,
            is_open=excursion.status is ExcursionStatus.gathering,
            registered_count=self.repo.count_registered(excursion_id),
            checked_in_count=len(checked_in),
            checked_in=checked_in if is_guide else [],
            my_checked_in_at=as_utc(me.checked_in_at) if registered and me.checked_in_at else None,
        )

    def open_gathering(self, excursion_id: str) -> Excursion:
        """Экскурсия, у которой прямо сейчас идёт сбор, — иначе ошибка."""
        excursion = self.get(excursion_id)
        if self._close_if_expired(excursion):
            self.db.commit()
            self._credit_excursion_completion(excursion)
        if excursion.status is not ExcursionStatus.gathering:
            raise Conflict("Сбор группы сейчас не идёт")
        return excursion

    @staticmethod
    def ensure_on_site(
        excursion: Excursion, *, lat: float, lon: float, accuracy_m: float | None
    ) -> None:
        distance = distance_m(lat, lon, excursion.lat, excursion.lon)
        # Погрешность GPS идёт в зачёт человеку, но не больше потолка: с точностью
        # «плюс-минус километр» бамп засчитывался бы из соседнего квартала.
        slack = min(accuracy_m or 0.0, settings.bump_accuracy_slack_m)
        radius = settings.excursion_site_radius_m
        if distance - slack > radius:
            raise Conflict(
                f"Вы в {round(distance)} м от места сбора — подойдите ближе "
                f"(нужно не дальше {round(radius)} м)"
            )

    # --- helpers ---

    def _views(
        self, principal: Principal | None, excursions: Sequence[Excursion]
    ) -> list[ExcursionView]:
        # Сначала закрыть все просроченные, потом проверить: `any` с генератором
        # остановился бы на первой и не закрыл остальные.
        closed = [self._close_if_expired(excursion) for excursion in excursions]
        if any(closed):
            self.db.commit()
            for excursion, was_closed in zip(excursions, closed, strict=True):
                if was_closed:
                    self._credit_excursion_completion(excursion)

        ids = [excursion.id for excursion in excursions]
        counts = self.repo.counts(ids)
        mine = self.repo.participations(principal.user_id, ids) if principal else {}

        views = []
        for excursion in excursions:
            registered_count, checked_in_count = counts.get(excursion.id, (0, 0))
            viewer = None
            if principal is not None:
                me = mine.get(excursion.id)
                registered = me is not None and me.status is RegistrationStatus.registered
                viewer = ViewerState(
                    is_guide=excursion.guide_id == principal.user_id,
                    registered=registered,
                    checked_in_at=as_utc(me.checked_in_at)
                    if registered and me.checked_in_at
                    else None,
                )
            views.append(ExcursionView(excursion, registered_count, checked_in_count, viewer))
        return views

    def _credit_excursion_completion(self, excursion: Excursion) -> None:
        """Статистика профиля («сколько сборов завершил») — краевед и
        отметившиеся бампом участники. Незарегистрированных пришедших не
        считаем — бамп без записи не отмечает, см. README."""
        stats_client.increment_stat(user_id=excursion.guide_id, metric="excursions_completed")
        for participant in self.repo.checked_in_for(excursion.id):
            stats_client.increment_stat(user_id=participant.user_id, metric="excursions_completed")

    @staticmethod
    def _close_if_expired(excursion: Excursion) -> bool:
        """Сбор, чей срок вышел, закрывается при первом обращении — фоновый планировщик не нужен."""
        if (
            excursion.status is ExcursionStatus.gathering
            and excursion.gathering_ends_at is not None
            and as_utc(excursion.gathering_ends_at) <= utcnow()
        ):
            excursion.status = ExcursionStatus.finished
            return True
        return False

    @staticmethod
    def _ensure_guide(principal: Principal, excursion: Excursion) -> None:
        if is_staff(principal) or excursion.guide_id == principal.user_id:
            return
        raise PermissionDenied("Управлять экскурсией может её краевед или модератор")
