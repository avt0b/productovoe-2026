"""Прогулка: собранная группа идёт за краеведом к памятному месту.

После бампа люди знают, что они вместе, но не знают, куда идти и где
остальные. Здесь краевед задаёт цель, а каждый телефон присылает свою точку и
получает точки всей группы — у всех на карте одна картина: кто где, где
краевед и куда он ведёт.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import Conflict, PermissionDenied
from core.models import (
    Excursion,
    ExcursionPosition,
    ExcursionStatus,
    ExcursionWalk,
    RegistrationStatus,
)
from core.security import Principal
from core.timeutil import as_utc, utcnow
from repositories.excursion_repository import ExcursionRepository
from services import achievement_client, notify_client
from services.excursion_service import ExcursionService
from services.permissions import is_staff

# Вид уведомления «группа вышла» — приложение по нему открывает карту.
KIND_WALK_STARTED = "excursion_walk_started"


@dataclass(frozen=True)
class GroupMember:
    user_id: str
    is_guide: bool
    is_me: bool
    lat: float
    lon: float
    accuracy_m: float | None
    updated_at: datetime


@dataclass(frozen=True)
class WalkState:
    excursion: Excursion
    # None — группа ещё не вышла или вышла без цели (не бывает: цель обязательна).
    walk: ExcursionWalk | None
    members: list[GroupMember]
    is_guide: bool


class WalkService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExcursionRepository(db)
        self.excursions = ExcursionService(db)

    # --- краевед ---

    def lead(
        self,
        principal: Principal,
        excursion_id: str,
        *,
        lat: float,
        lon: float,
        name: str,
        poi_id: str | None,
    ) -> WalkState:
        """Повести группу к месту — или сменить место, если группа уже идёт.

        Первый вызов закрывает сбор и рассылает отмеченным «Экскурсия
        началась». Следующие только меняют цель: краевед ведёт группу от
        памятника к памятнику, и будить всех уведомлением на каждом шаге —
        лишнее, карта и так обновится.
        """
        excursion = self.excursions.get(excursion_id)
        self._ensure_guide(principal, excursion)
        self._settle_expiry(excursion)

        if excursion.status is ExcursionStatus.scheduled:
            raise Conflict("Сначала соберите группу: откройте сбор и отметьте тех, кто пришёл")
        if excursion.status not in (ExcursionStatus.gathering, ExcursionStatus.walking):
            raise Conflict("Экскурсия уже завершена или отменена")

        now = utcnow()
        first_start = excursion.status is ExcursionStatus.gathering
        walk = self.db.get(ExcursionWalk, excursion_id)
        if walk is None:
            walk = ExcursionWalk(excursion_id=excursion_id, started_at=now, updated_at=now,
                                 destination_lat=lat, destination_lon=lon)
            self.db.add(walk)
        walk.destination_lat = lat
        walk.destination_lon = lon
        walk.destination_name = name
        walk.destination_poi_id = poi_id
        walk.updated_at = now
        if first_start:
            walk.started_at = now
            excursion.status = ExcursionStatus.walking
        self.db.commit()

        if first_start:
            self._announce(excursion, name)
            achievement_client.award_achievement(
                user_id=excursion.guide_id, code=achievement_client.HISTORIAN_LED_GROUP
            )
        return self.state(principal, excursion_id)

    def finish(self, principal: Principal, excursion_id: str) -> WalkState:
        excursion = self.excursions.get(excursion_id)
        self._ensure_guide(principal, excursion)
        if excursion.status is ExcursionStatus.walking:
            excursion.status = ExcursionStatus.finished
            self._forget_positions(excursion_id)
            self.db.commit()
            self.excursions._credit_excursion_completion(excursion)
        elif excursion.status is not ExcursionStatus.finished:
            raise Conflict("Группа ещё не выходила")
        return self.state(principal, excursion_id)

    # --- группа ---

    def state(self, principal: Principal, excursion_id: str) -> WalkState:
        excursion = self.excursions.get(excursion_id)
        is_guide = self._ensure_in_group(principal, excursion)
        self._settle_expiry(excursion)

        walk = self.db.get(ExcursionWalk, excursion_id)
        members: list[GroupMember] = []
        if excursion.status is ExcursionStatus.walking:
            fresh_after = utcnow() - timedelta(seconds=settings.walk_position_ttl_seconds)
            rows = self.db.scalars(
                select(ExcursionPosition).where(ExcursionPosition.excursion_id == excursion_id)
            ).all()
            members = [
                GroupMember(
                    user_id=row.user_id,
                    is_guide=row.is_guide,
                    is_me=row.user_id == principal.user_id,
                    lat=row.lat,
                    lon=row.lon,
                    accuracy_m=row.accuracy_m,
                    updated_at=as_utc(row.updated_at),
                )
                for row in rows
                if as_utc(row.updated_at) >= fresh_after
            ]
            # Краевед — первым: клиенту не искать его в списке.
            members.sort(key=lambda member: (not member.is_guide, member.user_id))
        return WalkState(excursion=excursion, walk=walk, members=members, is_guide=is_guide)

    def report_position(
        self,
        principal: Principal,
        excursion_id: str,
        *,
        lat: float,
        lon: float,
        accuracy_m: float | None,
    ) -> None:
        excursion = self.excursions.get(excursion_id)
        is_guide = self._ensure_in_group(principal, excursion)
        self._settle_expiry(excursion)
        if excursion.status is not ExcursionStatus.walking:
            raise Conflict("Группа сейчас не идёт — точку некому показывать")

        row = self.db.get(ExcursionPosition, (excursion_id, principal.user_id))
        if row is None:
            row = ExcursionPosition(excursion_id=excursion_id, user_id=principal.user_id,
                                    lat=lat, lon=lon, updated_at=utcnow())
            self.db.add(row)
        row.is_guide = is_guide
        row.lat = lat
        row.lon = lon
        row.accuracy_m = accuracy_m
        row.updated_at = utcnow()
        self.db.commit()

    # --- helpers ---

    def _ensure_in_group(self, principal: Principal, excursion: Excursion) -> bool:
        """Карту группы видят краевед и те, кто отметился бампом. Возвращает «краевед ли»."""
        if excursion.guide_id == principal.user_id or is_staff(principal):
            return True
        me = self.repo.get_participant(excursion.id, principal.user_id)
        if me is None or me.status is not RegistrationStatus.registered:
            raise PermissionDenied("Карта группы — для тех, кто записан на экскурсию")
        if me.checked_in_at is None:
            # Записался, но не пришёл: показывать ему, где группа, — значит
            # раскрывать, где ходят чужие люди, тому, кто с ними не был.
            raise PermissionDenied("Сначала отметьтесь у краеведа — встряхните телефоны рядом")
        return False

    def _settle_expiry(self, excursion: Excursion) -> None:
        """Сбор или прогулка вышли по сроку — закрыть и засчитать в статистику.

        Засчитывается ровно на переходе в `finished`, поэтому дважды не бывает:
        сбор, перешедший в прогулку, ещё не завершён и в зачёт не идёт.
        """
        if self._close_if_expired(excursion):
            self.db.commit()
            self.excursions._credit_excursion_completion(excursion)

    def _close_if_expired(self, excursion: Excursion) -> bool:
        """Сбор и прогулка, чей срок вышел, закрываются при первом обращении."""
        if ExcursionService._close_if_expired(excursion):
            return True
        if excursion.status is not ExcursionStatus.walking:
            return False
        walk = self.db.get(ExcursionWalk, excursion.id)
        started = as_utc(walk.started_at) if walk else None
        if started is None or started + timedelta(hours=settings.walk_duration_hours) > utcnow():
            return False
        excursion.status = ExcursionStatus.finished
        self._forget_positions(excursion.id)
        return True

    def _forget_positions(self, excursion_id: str) -> None:
        # Экскурсия кончилась — где ходили люди, больше никому не нужно знать.
        for row in self.db.scalars(
            select(ExcursionPosition).where(ExcursionPosition.excursion_id == excursion_id)
        ).all():
            self.db.delete(row)

    def _announce(self, excursion: Excursion, destination_name: str) -> None:
        """Отмеченным — «Экскурсия началась». Не пришедшим не пишем: карта не для них."""
        recipients = [
            participant.user_id
            for participant in self.repo.checked_in_for(excursion.id)
            if participant.status is RegistrationStatus.registered
        ]
        where = f"к «{destination_name}»" if destination_name else "к памятному месту"
        notify_client.notify_users(
            user_ids=recipients,
            kind=KIND_WALK_STARTED,
            title="Экскурсия началась",
            body=f"Группа идёт {where}. Откройте карту — на ней все свои и маршрут.",
            payload={"excursion_id": excursion.id},
        )

    @staticmethod
    def _ensure_guide(principal: Principal, excursion: Excursion) -> None:
        ExcursionService._ensure_guide(principal, excursion)
