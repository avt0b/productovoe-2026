from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.geo import haversine_km
from core.models import Route, Waypoint
from core.security import Principal
from repositories.route_repository import RouteRepository
from services import achievement_client
from services.map_client import fetch_poi_nearby

# Кто может создавать и вести маршруты (кураторы контента).
AUTHOR_ROLES = {"local_historian"}


def _can_author(principal: Principal) -> bool:
    return principal.is_root or principal.role in AUTHOR_ROLES


class RouteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RouteRepository(db)

    # --- чтение ---

    def get_visible(self, principal: Principal | None, route_id: str) -> Route:
        route = self.repo.get(route_id, with_waypoints=True)
        if route is None:
            raise NotFound("Маршрут не найден")
        if route.is_published:
            return route
        if principal and (self._is_staff(principal) or route.created_by == principal.user_id):
            return route
        raise NotFound("Маршрут не найден")

    def search_public(self, **filters) -> Sequence[Route]:
        filters["published_only"] = True
        return self.repo.search(**filters)

    def list_mine(self, principal: Principal, **filters) -> Sequence[Route]:
        return self.repo.search(created_by=principal.user_id, published_only=False, **filters)

    def waypoints_of(self, principal: Principal | None, route_id: str) -> Sequence[Waypoint]:
        self.get_visible(principal, route_id)
        return self.repo.waypoints_of(route_id)

    # --- маршрут ---

    def create(self, principal: Principal, data: dict) -> Route:
        if not _can_author(principal):
            raise PermissionDenied("Создавать маршруты могут краеведы")
        route = self.repo.add(Route(created_by=principal.user_id, **data))
        self.db.commit()
        self.db.refresh(route)
        return route

    async def auto_generate(self, principal: Principal, data: dict) -> Route:
        """Автосборка черновика: подтягивает точки слоя «ВОВ» из map_service
        рядом с (lat, lon) и раскладывает их в маршрут-прогулку (модуль 2 ТЗ).
        Контент точек (задания/аудио/AR) остаётся пустым — это ручная работа
        автора уже после автогенерации, здесь только расстановка на карте."""
        if not _can_author(principal):
            raise PermissionDenied("Создавать маршруты могут краеведы")

        lat, lon, radius_km = data["lat"], data["lon"], data["radius_km"]
        candidates = await fetch_poi_nearby(
            lat=lat, lon=lon, radius_km=radius_km, kind=data.get("kind"), limit=50
        )
        if not candidates:
            raise Conflict("Рядом с этой точкой нет точек слоя «ВОВ» — сначала нанесите их на карту")

        ordered = self._nearest_neighbor_order(lat, lon, candidates)[: data["max_points"]]
        distance_km = self._path_distance_km(lat, lon, ordered)

        title = data.get("title") or (
            f"Маршрут по «{data['city']}»" if data.get("city") else "Автомаршрут рядом с точкой"
        )
        route = self.repo.add(
            Route(
                created_by=principal.user_id,
                title=title,
                mode=data["mode"],
                city=data.get("city", ""),
                distance_km=round(distance_km, 2),
            )
        )
        for index, poi in enumerate(ordered):
            self.repo.add_waypoint(
                Waypoint(
                    route_id=route.id,
                    order_index=index,
                    title=poi["title"],
                    lat=poi["lat"],
                    lon=poi["lon"],
                    poi_id=poi["id"],
                    story=poi.get("description") or "",
                )
            )
        self.db.commit()
        return self.repo.get(route.id, with_waypoints=True)

    @staticmethod
    def _nearest_neighbor_order(lat: float, lon: float, candidates: list[dict]) -> list[dict]:
        """Жадный обход «от ближайшей точки к следующей ближайшей» — простой
        способ превратить набор точек в прогулочный маршрут, а не звезду лучей
        из одного центра (какой отдаёт map_service по умолчанию)."""
        remaining = list(candidates)
        path: list[dict] = []
        cur_lat, cur_lon = lat, lon
        while remaining:
            nearest = min(
                remaining, key=lambda p: haversine_km(cur_lat, cur_lon, p["lat"], p["lon"])
            )
            path.append(nearest)
            remaining.remove(nearest)
            cur_lat, cur_lon = nearest["lat"], nearest["lon"]
        return path

    @staticmethod
    def _path_distance_km(lat: float, lon: float, ordered: list[dict]) -> float:
        total = 0.0
        cur_lat, cur_lon = lat, lon
        for poi in ordered:
            total += haversine_km(cur_lat, cur_lon, poi["lat"], poi["lon"])
            cur_lat, cur_lon = poi["lat"], poi["lon"]
        return total

    def update(self, principal: Principal, route_id: str, data: dict) -> Route:
        route = self._get_editable(principal, route_id)
        for field, value in data.items():
            setattr(route, field, value)
        self.db.commit()
        self.db.refresh(route)
        return route

    def set_published(self, principal: Principal, route_id: str, published: bool) -> Route:
        route = self._get_editable(principal, route_id)
        if published and not self.repo.waypoints_of(route_id):
            raise Conflict("Нельзя опубликовать маршрут без точек")
        route.is_published = published
        self.db.commit()
        self.db.refresh(route)
        if published:
            achievement_client.award_achievement(
                user_id=route.created_by, code=achievement_client.HISTORIAN_ROUTE_AUTHOR
            )
        return route

    def delete(self, principal: Principal, route_id: str) -> None:
        route = self._get_editable(principal, route_id)
        self.repo.delete(route)
        self.db.commit()

    # --- точки маршрута ---

    def add_waypoint(self, principal: Principal, route_id: str, data: dict) -> Waypoint:
        self._get_editable(principal, route_id)
        order_index = data.pop("order_index", None)
        if order_index is None:
            order_index = self.repo.next_order_index(route_id)
        wp = self.repo.add_waypoint(Waypoint(route_id=route_id, order_index=order_index, **data))
        self.db.commit()
        self.db.refresh(wp)
        return wp

    def update_waypoint(self, principal: Principal, waypoint_id: str, data: dict) -> Waypoint:
        wp = self.repo.get_waypoint(waypoint_id)
        if wp is None:
            raise NotFound("Точка не найдена")
        self._get_editable(principal, wp.route_id)
        for field, value in data.items():
            setattr(wp, field, value)
        self.db.commit()
        self.db.refresh(wp)
        return wp

    def delete_waypoint(self, principal: Principal, waypoint_id: str) -> None:
        wp = self.repo.get_waypoint(waypoint_id)
        if wp is None:
            raise NotFound("Точка не найдена")
        self._get_editable(principal, wp.route_id)
        self.repo.delete_waypoint(wp)
        self.db.commit()

    def reorder_waypoints(
        self, principal: Principal, route_id: str, ordered_ids: list[str]
    ) -> Sequence[Waypoint]:
        self._get_editable(principal, route_id)
        by_id = {w.id: w for w in self.repo.waypoints_of(route_id)}
        if len(ordered_ids) != len(by_id) or set(ordered_ids) != set(by_id):
            raise NotFound("Список точек не совпадает с маршрутом")
        for index, wp_id in enumerate(ordered_ids):
            by_id[wp_id].order_index = index
        self.db.commit()
        return self.repo.waypoints_of(route_id)

    # --- helpers ---

    def _get_editable(self, principal: Principal, route_id: str) -> Route:
        route = self.repo.get(route_id)
        if route is None:
            raise NotFound("Маршрут не найден")
        if self._is_staff(principal) or route.created_by == principal.user_id:
            return route
        raise PermissionDenied("Редактировать маршрут может автор или администратор")

    @staticmethod
    def _is_staff(principal: Principal) -> bool:
        # Роль moderator убрана — стафф-права остались только у is_root.
        return principal.is_root
