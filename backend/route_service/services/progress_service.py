from datetime import UTC, datetime

from sqlalchemy.orm import Session

from core.exceptions import NotFound
from core.models import RouteProgress
from core.security import Principal
from repositories.progress_repository import ProgressRepository
from repositories.route_repository import RouteRepository


class ProgressService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProgressRepository(db)
        self.routes = RouteRepository(db)

    def start(self, principal: Principal, route_id: str) -> RouteProgress:
        route = self.routes.get(route_id)
        if route is None or not route.is_published:
            raise NotFound("Маршрут не найден")
        progress = self.repo.get(route_id, principal.user_id)
        if progress is None:
            progress = self.repo.add(RouteProgress(route_id=route_id, user_id=principal.user_id))
            self.db.commit()
            self.db.refresh(progress)
        return progress

    def get_mine(self, principal: Principal, route_id: str) -> RouteProgress:
        progress = self.repo.get(route_id, principal.user_id)
        if progress is None:
            raise NotFound("Маршрут ещё не начат")
        return progress

    def complete_waypoint(
        self, principal: Principal, route_id: str, waypoint_id: str
    ) -> RouteProgress:
        progress = self.start(principal, route_id)
        waypoints = self.routes.waypoints_of(route_id)
        ids = [w.id for w in waypoints]
        if waypoint_id not in ids:
            raise NotFound("Точка не принадлежит маршруту")

        done = set(progress.completed_waypoint_ids)
        done.add(waypoint_id)
        # Порядок по маршруту.
        progress.completed_waypoint_ids = [wid for wid in ids if wid in done]
        progress.current_index = min(len(progress.completed_waypoint_ids), len(ids))
        if len(done) >= len(ids) and ids:
            progress.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(progress)
        return progress
