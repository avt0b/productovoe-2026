from dataclasses import dataclass

from sqlalchemy.orm import Session

from core.security import Principal
from services.media_client import has_public_clip
from services.route_service import RouteService


@dataclass(frozen=True)
class MediaPrompt:
    waypoint_id: str
    poi_id: str
    title: str


class MediaPromptService:
    """«Пользователь у памятника/братской могилы — предложить оживить фото
    неизвестного бойца из этого захоронения» (п.7 ТЗ, интеграция «Живого
    фото» с маршрутами). Предлагаем только точки, у которых уже есть ссылка
    на POI слоя «ВОВ» и в media_service для неё ещё нет ни одного публичного
    клипа — иначе подсказка сыпалась бы на каждую точку с координатами."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.routes = RouteService(db)

    async def prompts_for_route(
        self, principal: Principal | None, route_id: str
    ) -> list[MediaPrompt]:
        route = self.routes.get_visible(principal, route_id)
        prompts: list[MediaPrompt] = []
        for wp in route.waypoints:
            if not wp.poi_id:
                continue
            if await has_public_clip(wp.poi_id):
                continue
            prompts.append(MediaPrompt(waypoint_id=wp.id, poi_id=wp.poi_id, title=wp.title))
        return prompts
