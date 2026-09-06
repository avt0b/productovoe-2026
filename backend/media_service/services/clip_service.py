from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import ClipShare, ClipStatus, MemorialClip
from core.security import Principal
from repositories.clip_repository import ClipRepository

STAFF_ROLES = {"moderator"}


def _is_staff(principal: Principal) -> bool:
    return principal.is_root or principal.role in STAFF_ROLES


class ClipService:
    """Жизненный цикл «Живого фото». Реальная генерация — за воркером
    (`render_next` / `mark_ready` / `mark_failed`); здесь только состояние.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ClipRepository(db)

    # --- чтение ---

    def get_visible(self, principal: Principal | None, clip_id: str) -> MemorialClip:
        clip = self.repo.get(clip_id)
        if clip is None:
            raise NotFound("Клип не найден")
        if clip.is_public and clip.status is ClipStatus.ready:
            return clip
        if principal and (_is_staff(principal) or clip.submitted_by == principal.user_id):
            return clip
        raise NotFound("Клип не найден")

    def public_gallery(self, **filters) -> Sequence[MemorialClip]:
        return self.repo.search(status=ClipStatus.ready, public_only=True, **filters)

    def list_mine(self, principal: Principal, **filters) -> Sequence[MemorialClip]:
        return self.repo.search(submitted_by=principal.user_id, **filters)

    # --- заявка ---

    def create(self, principal: Principal, data: dict) -> MemorialClip:
        if not data.get("consent_memorial_use"):
            raise PermissionDenied(
                "Технология доступна только для мемориального использования — нужно согласие"
            )
        clip = self.repo.add(
            MemorialClip(
                submitted_by=principal.user_id, status=ClipStatus.queued, **data
            )
        )
        self.db.commit()
        self.db.refresh(clip)
        return clip

    def update(self, principal: Principal, clip_id: str, data: dict) -> MemorialClip:
        clip = self._owned_or_staff(principal, clip_id)
        if clip.status in (ClipStatus.processing, ClipStatus.ready) and not _is_staff(principal):
            raise Conflict("Клип уже в работе — текст и голос менять нельзя")
        for field, value in data.items():
            setattr(clip, field, value)
        self.db.commit()
        self.db.refresh(clip)
        return clip

    def delete(self, principal: Principal, clip_id: str) -> None:
        clip = self._owned_or_staff(principal, clip_id)
        self.repo.delete(clip)
        self.db.commit()

    def retry(self, principal: Principal, clip_id: str) -> MemorialClip:
        clip = self._owned_or_staff(principal, clip_id)
        if clip.status is not ClipStatus.failed:
            raise Conflict("Повторить можно только неудавшуюся генерацию")
        clip.status = ClipStatus.queued
        clip.error = ""
        self.db.commit()
        self.db.refresh(clip)
        return clip

    # --- «Отправить родным» ---

    def share(self, principal: Principal, clip_id: str, *, recipient: str, note: str) -> ClipShare:
        clip = self._owned_or_staff(principal, clip_id)
        if clip.status is not ClipStatus.ready:
            raise Conflict("Отправить можно только готовый клип")
        share = self.repo.add_share(
            ClipShare(
                clip_id=clip_id, shared_by=principal.user_id, recipient=recipient, note=note
            )
        )
        self.db.commit()
        self.db.refresh(share)
        return share

    def shares_of(self, principal: Principal, clip_id: str) -> Sequence[ClipShare]:
        self._owned_or_staff(principal, clip_id)
        return self.repo.shares_of(clip_id)

    # --- воркер рендера (переходы состояний) ---

    def claim_next(self) -> MemorialClip | None:
        clip = self.repo.oldest_queued()
        if clip is None:
            return None
        clip.status = ClipStatus.processing
        self.db.commit()
        self.db.refresh(clip)
        return clip

    def mark_ready(self, clip_id: str, *, video_url: str) -> MemorialClip:
        clip = self._require(clip_id)
        clip.status = ClipStatus.ready
        clip.video_url = video_url
        clip.error = ""
        clip.rendered_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(clip)
        return clip

    def mark_failed(self, clip_id: str, *, error: str) -> MemorialClip:
        clip = self._require(clip_id)
        clip.status = ClipStatus.failed
        clip.error = error
        self.db.commit()
        self.db.refresh(clip)
        return clip

    # --- helpers ---

    def _require(self, clip_id: str) -> MemorialClip:
        clip = self.repo.get(clip_id)
        if clip is None:
            raise NotFound("Клип не найден")
        return clip

    def _owned_or_staff(self, principal: Principal, clip_id: str) -> MemorialClip:
        clip = self._require(clip_id)
        if _is_staff(principal) or clip.submitted_by == principal.user_id:
            return clip
        raise PermissionDenied("Доступ только у автора клипа или модератора")
