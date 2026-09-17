"""Демо-маршрут «Тропа памяти: центр Орла» — сценарий кейса «мама с ребёнком 10 лет».

Запуск из `backend/route_service`:

    uv run python -m scripts.seed_orel

Идемпотентный: id постоянные (uuid5), повторный запуск обновляет тот же маршрут.
Схему создаёт сам.

Четыре точки — реальные мемориалы центра Орла, координаты из OpenStreetMap.
`poi_id` каждой точки совпадает с id того же места в `map_service`
(`scripts/seed_orel.py` там): неймспейс uuid5 у скриптов общий, поэтому
ссылки сходятся без запросов между сервисами.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from core.models import Route, RouteMode, Waypoint

SEED_AUTHOR = "seed-orel"

# Тот же неймспейс, что в map_service/scripts/seed_orel.py. Менять только вместе.
SEED_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "marshruty/seed/orel")


def seed_id(kind: str, key: str) -> str:
    return str(uuid.uuid5(SEED_NAMESPACE, f"{kind}:{key}"))


ROUTE_KEY = "orel-family-trail"


@dataclass(frozen=True)
class WaypointSeed:
    key: str
    poi_key: str
    title: str
    lat: float
    lon: float
    story: str
    kid_task: str
    ar_hint: str


WAYPOINTS: tuple[WaypointSeed, ...] = (
    WaypointSeed(
        key="artillery",
        poi_key="orel-artillery",
        title="Памятник воинам-артиллеристам",
        lat=52.964565,
        lon=36.064246,
        story=(
            "Начинаем у памятника артиллеристам. Без огня артиллерии пехота и танки "
            "не смогли бы прорвать оборону — недаром её называли «богом войны»."
        ),
        kid_task="Найди на памятнике надпись или год и запиши в блокнот исследователя.",
        ar_hint="Наведи камеру на памятник — проводник расскажет, как работал расчёт орудия.",
    ),
    WaypointSeed(
        key="liberators",
        poi_key="orel-liberators",
        title="«Освободителям Орла в 1943 г.»",
        lat=52.968336,
        lon=36.069922,
        story=(
            "5 августа 1943 года Орёл освободили. В тот же вечер в Москве впервые за войну "
            "прогремел салют — в честь освобождения Орла и Белгорода."
        ),
        kid_task="Сколько лет прошло с освобождения Орла? Посчитай вместе с родителями.",
        ar_hint="Найди на памятнике дату освобождения — AR покажет салют 1943 года.",
    ),
    WaypointSeed(
        key="t34",
        poi_key="orel-t34",
        title="Танк Т-34-85",
        lat=52.967596,
        lon=36.077005,
        story=(
            "Т-34 — самый массовый советский танк войны. Модификация Т-34-85 получила "
            "пушку калибра 85 мм, отсюда и цифра в названии. Экипаж — пять человек."
        ),
        kid_task="Найди калибр пушки: подсказка спрятана в названии танка.",
        ar_hint="Встань перед танком — AR покажет, где внутри сидел каждый из пяти танкистов.",
    ),
    WaypointSeed(
        key="mass-grave",
        poi_key="orel-mass-grave",
        title="Вечный огонь и братская могила",
        lat=52.967986,
        lon=36.078488,
        story=(
            "Здесь похоронены воины, погибшие при освобождении города. "
            "Минута молчания — главное задание маршрута."
        ),
        kid_task="Постойте минуту в тишине. Если хотите — положите цветы.",
        # У могилы AR не включаем: это место тишины, а не аттракцион.
        ar_hint="",
    ),
)


def seed(db: Session) -> dict[str, int]:
    """Залить демо-маршрут с точками. Возвращает размеры демо-набора."""
    route_id = seed_id("route", ROUTE_KEY)
    db.merge(
        Route(
            id=route_id,
            title="Тропа памяти: центр Орла",
            description=(
                "Семейная прогулка по местам памяти освободителей Орла: четыре точки, "
                "задания для ребёнка и AR-подсказки."
            ),
            mode=RouteMode.family,
            city="Орёл",
            # Пешком по улицам между точками, а не по прямой.
            distance_km=1.5,
            cover_url=None,
            created_by=SEED_AUTHOR,
            is_published=True,
        )
    )
    for index, item in enumerate(WAYPOINTS):
        db.merge(
            Waypoint(
                id=seed_id("waypoint", f"{ROUTE_KEY}:{item.key}"),
                route_id=route_id,
                order_index=index,
                title=item.title,
                lat=item.lat,
                lon=item.lon,
                poi_id=seed_id("poi", item.poi_key),
                story=item.story,
                kid_task=item.kid_task,
                audio_url=None,
                ar_hint=item.ar_hint,
            )
        )
    db.commit()
    return {"routes": 1, "waypoints": len(WAYPOINTS)}


def main() -> None:
    from core.db import SessionLocal, init_db

    init_db()
    with SessionLocal() as db:
        counts = seed(db)
    print(f"route_service: маршрутов — {counts['routes']}, точек — {counts['waypoints']}")


if __name__ == "__main__":
    main()
