from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import ApplicationStatus, RoleApplication


class RoleApplicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, application_id: str) -> RoleApplication | None:
        return self.db.get(RoleApplication, application_id)

    def add(self, application: RoleApplication) -> RoleApplication:
        self.db.add(application)
        self.db.flush()
        return application

    def for_user(self, user_id: str) -> Sequence[RoleApplication]:
        return self.db.scalars(
            select(RoleApplication)
            .where(RoleApplication.user_id == user_id)
            .order_by(RoleApplication.created_at.desc())
        ).all()

    def pending(self, user_id: str, requested_role: str | None = None) -> RoleApplication | None:
        """Нерассмотренная заявка человека: на указанную роль или на любую."""
        stmt = select(RoleApplication).where(
            RoleApplication.user_id == user_id,
            RoleApplication.status == ApplicationStatus.pending,
        )
        if requested_role is not None:
            stmt = stmt.where(RoleApplication.requested_role == requested_role)
        return self.db.scalars(stmt.order_by(RoleApplication.created_at.asc())).first()

    def search(
        self, *, status: ApplicationStatus | None = None, limit: int = 50, offset: int = 0
    ) -> Sequence[RoleApplication]:
        stmt = select(RoleApplication)
        if status is not None:
            stmt = stmt.where(RoleApplication.status == status)
        stmt = stmt.order_by(RoleApplication.created_at.desc()).limit(limit).offset(offset)
        return self.db.scalars(stmt).all()
