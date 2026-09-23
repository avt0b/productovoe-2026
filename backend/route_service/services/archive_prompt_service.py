from dataclasses import dataclass

from sqlalchemy.orm import Session

from core.config import settings
from core.geo import bbox_covering, haversine_km
from core.models import Waypoint
from core.security import Principal
from services.archive_client import fetch_nearby_pending
from services.route_service import RouteService


@dataclass(frozen=True)
class ArchivePrompt:
    waypoint_id: str
    entry_id: str
    kind: str
    title: str
    distance_km: float


class ArchivePromptService:
    """«Рядом с точкой маршрута есть неподтверждённая краеведческая заметка —
    помоги проверить» (п.5 ТЗ, интеграция архива с основными маршрутами)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.routes = RouteService(db)

    async def prompts_for_route(
        self, principal: Principal | None, route_id: str
    ) -> list[ArchivePrompt]:
        route = self.routes.get_visible(principal, route_id)
        waypoints = list(route.waypoints)
        if not waypoints:
            return []

        radius_km = settings.archive_nearby_radius_km
        bbox = bbox_covering([(wp.lat, wp.lon) for wp in waypoints], radius_km)
        entries = await fetch_nearby_pending(bbox)

        prompts: list[ArchivePrompt] = []
        for entry in entries:
            if entry.get("lat") is None or entry.get("lon") is None:
                continue
            nearest = self._nearest_waypoint(waypoints, entry["lat"], entry["lon"])
            if nearest is None:
                continue
            waypoint, distance_km = nearest
            if distance_km > radius_km:
                continue
            prompts.append(
                ArchivePrompt(
                    waypoint_id=waypoint.id,
                    entry_id=entry["id"],
                    kind=entry["kind"],
                    title=entry["title"],
                    distance_km=round(distance_km, 3),
                )
            )
        return prompts

    @staticmethod
    def _nearest_waypoint(
        waypoints: list[Waypoint], lat: float, lon: float
    ) -> tuple[Waypoint, float] | None:
        best: tuple[Waypoint, float] | None = None
        for wp in waypoints:
            distance_km = haversine_km(lat, lon, wp.lat, wp.lon)
            if best is None or distance_km < best[1]:
                best = (wp, distance_km)
        return best
