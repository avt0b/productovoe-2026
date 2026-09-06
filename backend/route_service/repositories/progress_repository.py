from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import RouteProgress


class ProgressRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, route_id: str, user_id: str) -> RouteProgress | None:
        return self.db.scalar(
            select(RouteProgress).where(
                RouteProgress.route_id == route_id, RouteProgress.user_id == user_id
            )
        )

    def add(self, progress: RouteProgress) -> RouteProgress:
        self.db.add(progress)
        self.db.flush()
        return progress
