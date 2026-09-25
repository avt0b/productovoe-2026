import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.geo import bbox_around, haversine_km
from core.models import ArchiveEntry, EntryKind, EntryStatus
from core.security import Principal
from repositories.entry_repository import EntryRepository
from services import achievement_client
from services.achievement_client import award_achievement
from services.stats_client import increment_stat

logger = logging.getLogger(__name__)

# Кто может верифицировать записи (поисковик / краевед).
VERIFIER_ROLES = {"searcher", "local_historian"}
ACHIEVEMENT_ARCHIVE_HELPER = "archive_helper"
# Сколько подтверждённых записей делает краеведа «Хранителем архива».
ARCHIVE_KEEPER_THRESHOLD = 10
STAT_FINDS_COUNT = "finds_count"


def _can_verify(principal: Principal) -> bool:
    return principal.is_root or principal.role in VERIFIER_ROLES


class EntryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EntryRepository(db)

    # --- чтение ---

    def get_visible(self, principal: Principal | None, entry_id: str) -> ArchiveEntry:
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFound
        if entry.status is EntryStatus.verified:
            return entry
        # неопубликованное видят автор и верификаторы
        if principal and (_can_verify(principal) or entry.submitted_by == principal.user_id):
            return entry
        raise NotFound

    def search_public(self, **filters) -> Sequence[ArchiveEntry]:
        filters.setdefault("status", EntryStatus.verified)
        return self.repo.search(**filters)

    def summary_public(self, *, kind: EntryKind | None = None) -> dict:
        return self.repo.summary(status=EntryStatus.verified, kind=kind)

    def search_moderation(
        self, principal: Principal, *, status: EntryStatus | None = None, **filters
    ) -> Sequence[ArchiveEntry]:
        if not _can_verify(principal):
            raise PermissionDenied("Очередь модерации доступна поисковикам и краеведам")
        return self.repo.search(status=status, **filters)

    def list_mine(self, principal: Principal, **filters) -> Sequence[ArchiveEntry]:
        return self.repo.search(submitted_by=principal.user_id, **filters)

    def search_nearby_pending(
        self,
        *,
        bbox: tuple[float, float, float, float] | None = None,
        center: tuple[float, float] | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> Sequence[ArchiveEntry]:
        """Публичная витрина без прав верификатора — намеренно куцая (см. EntryNearbyOut).

        Круг (`center` + `radius_km`) — основной путь: «рядом есть
        неподтверждённая заметка» — это про расстояние, а не про угол
        прямоугольника, где на тех же 10 км по диагонали набегает 14. Рамка
        остаётся ради совместимости с теми, кто уже ходит с bbox.

        Рамка вокруг круга — предфильтр в SQL, точное расстояние досчитываем
        haversine и по нему же сортируем: ближняя запись человеку полезнее.
        """
        if center is not None and radius_km is not None:
            lat, lon = center
            rows = self.repo.search(
                status=EntryStatus.pending,
                bbox=bbox_around(lat, lon, radius_km),
                # Из рамки в круг попадает не всё: берём запас, режем после досчёта.
                limit=min(limit * 4, 800),
            )
            within = [
                (haversine_km(lat, lon, entry.lat, entry.lon), entry)
                for entry in rows
                if entry.lat is not None and entry.lon is not None
            ]
            within = [pair for pair in within if pair[0] <= radius_km]
            within.sort(key=lambda pair: pair[0])
            return [entry for _, entry in within[:limit]]

        return self.repo.search(status=EntryStatus.pending, bbox=bbox, limit=limit)

    # --- запись ---

    def create(self, principal: Principal, data: dict) -> ArchiveEntry:
        entry = self.repo.add(
            ArchiveEntry(submitted_by=principal.user_id, status=EntryStatus.pending, **data)
        )
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, principal: Principal, entry_id: str, data: dict) -> ArchiveEntry:
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFound
        is_author = entry.submitted_by == principal.user_id
        if not (is_author or _can_verify(principal)):
            raise PermissionDenied("Редактировать запись может автор или верификатор")
        if is_author and not _can_verify(principal) and entry.status is not EntryStatus.pending:
            raise Conflict("Проверенную запись автор менять не может")
        was_reviewed = entry.status is not EntryStatus.pending
        for field, value in data.items():
            setattr(entry, field, value)
        if _can_verify(principal) and was_reviewed:
            # Правку уже проверенной записи переносим в те же поля, что и
            # verify/reject — иначе reviewed_at/verified_by продолжали бы
            # указывать на исходную проверку, а не на того, кто последним
            # менял уже опубликованное содержание.
            entry.verified_by = principal.user_id
            entry.reviewed_at = datetime.now(UTC)
            logger.info(
                "archive entry %s edited after review by %s (status=%s)",
                entry_id,
                principal.user_id,
                entry.status.value,
            )
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def verify(self, principal: Principal, entry_id: str, *, note: str = "") -> ArchiveEntry:
        return self._review(principal, entry_id, EntryStatus.verified, note)

    def reject(self, principal: Principal, entry_id: str, *, note: str = "") -> ArchiveEntry:
        return self._review(principal, entry_id, EntryStatus.rejected, note)

    def delete(self, principal: Principal, entry_id: str) -> None:
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFound
        is_author = entry.submitted_by == principal.user_id
        if not (_can_verify(principal) or (is_author and entry.status is EntryStatus.pending)):
            raise PermissionDenied("Удалить запись может верификатор или автор (пока на проверке)")
        if entry.status is not EntryStatus.pending:
            # Удаление уже проверенной (в т.ч. публичной) записи необратимо и
            # не оставляет строки в БД — единственный оставшийся след здесь.
            logger.warning(
                "archive entry %s (status=%s, submitted_by=%s) deleted by %s",
                entry_id,
                entry.status.value,
                entry.submitted_by,
                principal.user_id,
            )
        self.repo.delete(entry)
        self.db.commit()

    # --- helpers ---

    def _review(
        self, principal: Principal, entry_id: str, status: EntryStatus, note: str
    ) -> ArchiveEntry:
        if not _can_verify(principal):
            raise PermissionDenied(
                "Проверять записи могут поисковики, краеведы, наставники и модераторы"
            )
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFound
        entry.status = status
        entry.verified_by = principal.user_id
        entry.reviewed_at = datetime.now(UTC)
        entry.review_note = note
        self.db.commit()
        self.db.refresh(entry)
        award_achievement(user_id=principal.user_id, code=ACHIEVEMENT_ARCHIVE_HELPER)
        if status is EntryStatus.verified:
            increment_stat(user_id=entry.submitted_by, metric=STAT_FINDS_COUNT)
            if self.repo.count_verified_by(principal.user_id) >= ARCHIVE_KEEPER_THRESHOLD:
                achievement_client.award_achievement(
                    user_id=principal.user_id, code=achievement_client.HISTORIAN_ARCHIVE_KEEPER
                )
        return entry
