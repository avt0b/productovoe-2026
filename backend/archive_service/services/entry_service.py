import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import ArchiveEntry, EntryStatus
from core.security import Principal
from repositories.entry_repository import EntryRepository

logger = logging.getLogger(__name__)

# Кто может верифицировать записи (краевед / наставник / модератор).
VERIFIER_ROLES = {"local_historian", "mentor", "moderator"}


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

    def search_moderation(
        self, principal: Principal, *, status: EntryStatus | None = None, **filters
    ) -> Sequence[ArchiveEntry]:
        if not _can_verify(principal):
            raise PermissionDenied("Очередь модерации доступна краеведам и модераторам")
        return self.repo.search(status=status, **filters)

    def list_mine(self, principal: Principal, **filters) -> Sequence[ArchiveEntry]:
        return self.repo.search(submitted_by=principal.user_id, **filters)

    def search_nearby_pending(
        self, *, bbox: tuple[float, float, float, float], limit: int = 100
    ) -> Sequence[ArchiveEntry]:
        """Публичная витрина без прав верификатора — намеренно куцая (см. EntryNearbyOut)."""
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
            raise PermissionDenied("Проверять записи могут краеведы, наставники и модераторы")
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFound
        entry.status = status
        entry.verified_by = principal.user_id
        entry.reviewed_at = datetime.now(UTC)
        entry.review_note = note
        self.db.commit()
        self.db.refresh(entry)
        return entry
