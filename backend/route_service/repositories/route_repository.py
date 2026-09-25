from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.models import Route, RouteMode, Waypoint


class RouteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, route_id: str, *, with_waypoints: bool = False) -> Route | None:
        if with_waypoints:
            return self.db.scalar(
                select(Route).where(Route.id == route_id).options(selectinload(Route.waypoints))
            )
        return self.db.get(Route, route_id)

    def add(self, route: Route) -> Route:
        self.db.add(route)
        self.db.flush()
        return route

    def delete(self, route: Route) -> None:
        self.db.delete(route)

    def search(
        self,
        *,
        mode: RouteMode | None = None,
        city: str | None = None,
        published_only: bool = True,
        created_by: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Route]:
        stmt = select(Route)
        if mode is not None:
            stmt = stmt.where(Route.mode == mode)
        if city:
            stmt = stmt.where(Route.city.ilike(f"%{city}%"))
        if published_only:
            stmt = stmt.where(Route.is_published.is_(True))
        if created_by is not None:
            stmt = stmt.where(Route.created_by == created_by)
        return self.db.scalars(
            stmt.order_by(Route.created_at.desc()).limit(limit).offset(offset)
        ).all()

    # --- waypoints ---

    def get_waypoint(self, waypoint_id: str) -> Waypoint | None:
        return self.db.get(Waypoint, waypoint_id)

    def add_waypoint(self, waypoint: Waypoint) -> Waypoint:
        self.db.add(waypoint)
        self.db.flush()
        return waypoint

    def delete_waypoint(self, waypoint: Waypoint) -> None:
        self.db.delete(waypoint)

    def waypoints_of(self, route_id: str) -> Sequence[Waypoint]:
        return self.db.scalars(
            select(Waypoint).where(Waypoint.route_id == route_id).order_by(Waypoint.order_index)
        ).all()

    def next_order_index(self, route_id: str) -> int:
        rows = self.waypoints_of(route_id)
        return (max((w.order_index for w in rows), default=-1)) + 1
