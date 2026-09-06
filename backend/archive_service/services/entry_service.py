from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import ArchiveEntry, EntryStatus
from core.security import Principal
from repositories.entry_repository import EntryRepository

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
        if principal and (
            _can_verify(principal) or entry.submitted_by == principal.user_id
        ):
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

    # --- запись ---

    def create(self, principal: Principal, data: dict) -> ArchiveEntry:
        entry = self.repo.add(
            ArchiveEntry(
                submitted_by=principal.user_id, status=EntryStatus.pending, **data
            )
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
        for field, value in data.items():
            setattr(entry, field, value)
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
