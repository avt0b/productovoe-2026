from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session

from core.exceptions import PermissionDenied
from core.models import RegistrationStatus
from core.security import Principal
from core.timeutil import as_utc, utcnow
from repositories.excursion_repository import ExcursionRepository
from services.bump_matcher import BumpMatcher, Shake, bump_matcher
from services.excursion_service import ExcursionService

BumpOutcome = Literal["matched", "no_pair", "already_checked_in"]


@dataclass(frozen=True)
class BumpResult:
    result: BumpOutcome
    # С кем совпали: участнику — краевед, краеведу — участники.
    matched_user_ids: list[str] = field(default_factory=list)
    # Когда участника отметили пришедшим. У краеведа — None.
    checked_in_at: datetime | None = None
    checked_in_count: int = 0


class BumpService:
    """Бамп: встряска телефона на месте экскурсии отмечает, что участник пришёл."""

    def __init__(self, db: Session, matcher: BumpMatcher = bump_matcher) -> None:
        self.db = db
        self.repo = ExcursionRepository(db)
        self.excursions = ExcursionService(db)
        self.matcher = matcher

    def bump(
        self,
        principal: Principal,
        excursion_id: str,
        *,
        lat: float,
        lon: float,
        accuracy_m: float | None,
        shaken_ms_ago: int,
    ) -> BumpResult:
        # Время встряски считаем по часам сервера: часы телефонов расходятся на
        # секунды, а телефон знает только «тряхнули N мс назад».
        shaken_at = self.matcher.now() - shaken_ms_ago / 1000

        excursion = self.excursions.open_gathering(excursion_id)
        is_guide = excursion.guide_id == principal.user_id

        if not is_guide:
            participant = self.repo.get_participant(excursion_id, principal.user_id)
            if participant is None or participant.status is not RegistrationStatus.registered:
                raise PermissionDenied("Вы не записаны на эту экскурсию")
            if participant.checked_in_at is not None:
                return BumpResult(
                    result="already_checked_in",
                    matched_user_ids=[excursion.guide_id],
                    checked_in_at=as_utc(participant.checked_in_at),
                    checked_in_count=self.repo.count_checked_in(excursion_id),
                )

        self.excursions.ensure_on_site(excursion, lat=lat, lon=lon, accuracy_m=accuracy_m)

        # Пока ждём пару (до пары секунд), соединение с базой держать незачем:
        # вернуть его в пул, иначе толпа трясущих выберет все соединения.
        self.db.rollback()

        matches = self.matcher.shake(
            Shake(
                excursion_id=excursion_id,
                user_id=principal.user_id,
                is_guide=is_guide,
                shaken_at=shaken_at,
            )
        )
        matched_user_ids = list(dict.fromkeys(match.user_id for match in matches))
        if not matched_user_ids:
            return BumpResult(
                result="no_pair", checked_in_count=self.repo.count_checked_in(excursion_id)
            )

        checked_in_at = None if is_guide else self._check_in(excursion_id, principal.user_id)
        return BumpResult(
            result="matched",
            matched_user_ids=matched_user_ids,
            checked_in_at=checked_in_at,
            checked_in_count=self.repo.count_checked_in(excursion_id),
        )

    def _check_in(self, excursion_id: str, user_id: str) -> datetime | None:
        # Отметку ставит запрос участника: краевед мог совпасть с несколькими
        # людьми сразу, а каждый участник отвечает только за себя.
        participant = self.repo.get_participant(excursion_id, user_id)
        if participant is None:
            return None
        if participant.checked_in_at is None:
            participant.checked_in_at = utcnow()
            self.db.commit()
        return as_utc(participant.checked_in_at)
