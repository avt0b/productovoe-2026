"""Демо-наполнение карты по Орловской области: слой «ВОВ» и «Последний бой».

Запуск из `backend/map_service`:

    uv run python -m scripts.seed_orel

Скрипт идемпотентный: у каждой точки постоянный id (uuid5 от ключа), повторный
запуск обновляет те же строки, а не плодит дубли. Схему создаёт сам — сервис
перед этим запускать не нужно.

Откуда данные:

- **Слой «ВОВ»** — реальные места. Координаты мемориалов Орла взяты из
  OpenStreetMap. Для сёл и городов области стоят координаты самого населённого
  пункта — точное место памятника нужно уточнить у краеведов, это сказано в
  `source`.
- **«Последний бой»** — ДЕМО по сценариям кейса: «Иванов И. И., овраг у
  Крупышино», три десантника 9-й бригады от отряда «Высота». Это не архивные
  записи. `source` у каждой точки начинается с «ДЕМО», чтобы их не приняли за
  Книгу Памяти.
"""

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from core.models import LastStandPoint, LastStandStatus, POIKind, PointOfInterest

# Автор демо-строк. Не UUID пользователя — по нему демо легко найти и удалить.
SEED_AUTHOR = "seed-orel"

# Пространство имён id демо-данных. Тот же неймспейс в route_service: точки
# маршрута ссылаются на эти POI по `poi_id`, не делая запросов между сервисами.
SEED_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "marshruty/seed/orel")


def seed_id(kind: str, key: str) -> str:
    return str(uuid.uuid5(SEED_NAMESPACE, f"{kind}:{key}"))


OSM = "OpenStreetMap — координаты объекта"
SETTLEMENT = "координаты — центр населённого пункта, точное место уточнить"


@dataclass(frozen=True)
class PoiSeed:
    key: str
    kind: POIKind
    title: str
    description: str
    lat: float
    lon: float
    source: str
    event_date: date | None = None
    date_text: str = ""


POI: tuple[PoiSeed, ...] = (
    # --- Орёл, площадь Мира и центр ---
    PoiSeed(
        key="orel-mass-grave",
        kind=POIKind.grave,
        title="Братская могила на площади Мира",
        description=(
            "Здесь похоронены воины, погибшие при освобождении Орла в августе 1943 года, "
            "в основном танкисты. Рядом горит Вечный огонь."
        ),
        lat=52.967986,
        lon=36.078488,
        event_date=date(1943, 8, 5),
        date_text="5 августа 1943",
        source=OSM,
    ),
    PoiSeed(
        key="orel-eternal-flame",
        kind=POIKind.monument,
        title="Вечный огонь",
        description="Мемориал на площади Мира у братской могилы освободителей Орла.",
        lat=52.967558,
        lon=36.076835,
        source=OSM,
    ),
    PoiSeed(
        key="orel-t34",
        kind=POIKind.monument,
        title="Танк Т-34-85",
        description="Танк-памятник на площади Мира, рядом с братской могилой освободителей города.",
        lat=52.967596,
        lon=36.077005,
        source=OSM,
    ),
    PoiSeed(
        key="orel-liberators",
        kind=POIKind.monument,
        title="«Освободителям Орла в 1943 г.»",
        description="Памятник воинам, освободившим город 5 августа 1943 года.",
        lat=52.968336,
        lon=36.069922,
        event_date=date(1943, 8, 5),
        date_text="5 августа 1943",
        source=OSM,
    ),
    PoiSeed(
        key="orel-artillery",
        kind=POIKind.monument,
        title="Памятник воинам-артиллеристам",
        description="Мемориал воинам-артиллеристам в центре Орла.",
        lat=52.964565,
        lon=36.064246,
        source=OSM,
    ),
    PoiSeed(
        key="orel-civilians",
        kind=POIKind.grave,
        title="Место захоронения мирных жителей",
        description=(
            "По надписи на памятнике здесь захоронены около 500 советских граждан, "
            "замученных и расстрелянных фашистами в годы оккупации Орла."
        ),
        lat=52.980503,
        lon=36.065695,
        date_text="октябрь 1941 — август 1943",
        source=OSM,
    ),
    PoiSeed(
        key="orel-paratroopers",
        kind=POIKind.monument,
        title="Сквер Героев-десантников",
        description=(
            "3 октября 1941 года на Орловском аэродроме под огнём противника высадилась "
            "201-я воздушно-десантная бригада 5-го воздушно-десантного корпуса. "
            "В сквере — храм-часовня Александра Невского в память о погибших десантниках."
        ),
        lat=52.927049,
        lon=36.023937,
        event_date=date(1941, 10, 3),
        date_text="3 октября 1941",
        source=f"{OSM}; аудиогид ЦБС г. Орла",
    ),
    PoiSeed(
        key="orel-military-museum",
        kind=POIKind.other,
        title="Военно-исторический музей",
        description="Музей военной истории Орла — удобная точка сбора школьных и семейных экскурсий.",
        lat=52.953974,
        lon=36.062678,
        source=OSM,
    ),
    # --- Область ---
    PoiSeed(
        key="mtsensk-1941",
        kind=POIKind.battle,
        title="Бои под Мценском",
        description=(
            "В октябре 1941 года под Мценском 4-я танковая бригада М. Е. Катукова вместе "
            "с частями 5-го воздушно-десантного корпуса задерживала наступление "
            "танковых соединений Гудериана на Тулу."
        ),
        lat=53.278984,
        lon=36.576077,
        date_text="октябрь 1941",
        source=SETTLEMENT,
    ),
    PoiSeed(
        key="kromy-1943",
        kind=POIKind.battle,
        title="Кромы — полоса Орловской операции",
        description=(
            "Летом 1943 года Кромской район оказался в полосе наступления "
            "Орловской операции «Кутузов»."
        ),
        lat=52.689445,
        lon=35.773659,
        date_text="лето 1943",
        source=SETTLEMENT,
    ),
    PoiSeed(
        key="krupyshino-sailors",
        kind=POIKind.monument,
        title="Памятник морякам-тихоокеанцам у Крупышино",
        description=(
            "Открыт в 1978 году в память о моряках Тихоокеанского флота из 1-й отдельной "
            "лыжной бригады, погибших в боях на территории Дмитровского района зимой "
            "1943 года. Стоит у въезда в село, на дороге к Дмитровску-Орловскому."
        ),
        lat=52.568295,
        lon=35.487392,
        date_text="зима 1943",
        source=f"Госкомпания «Автодор»; {SETTLEMENT}",
    ),
    PoiSeed(
        key="khotynets-normandie",
        kind=POIKind.battle,
        title="Хотынец: лётчики «Нормандии»",
        description=(
            "В боях за освобождение Хотынца в августе 1943 года вместе с советскими "
            "лётчиками воевали французские пилоты эскадрильи «Нормандия»."
        ),
        lat=53.124597,
        lon=35.404486,
        date_text="август 1943",
        source=f"КиберЛенинка, «Память о французской эскадрилье»; {SETTLEMENT}",
    ),
    PoiSeed(
        key="semenkovo-trenches",
        kind=POIKind.trench,
        title="Семенково: район полевого выезда",
        description=(
            "Точка из сценария кейса «Выходные с поисковиком» — раскопки у д. Семенково. "
            "Линию окопов нужно уточнить у отряда."
        ),
        lat=52.581748,
        lon=35.954344,
        source=f"ДЕМО по кейсу; {SETTLEMENT}",
    ),
)


@dataclass(frozen=True)
class LastStandSeed:
    key: str
    status: LastStandStatus
    soldier_name: str
    unit: str
    lat: float
    lon: float
    circumstances: str
    date_text: str
    source: str
    death_date: date | None = None


LAST_STAND: tuple[LastStandSeed, ...] = (
    LastStandSeed(
        key="krupyshino-ivanov",
        status=LastStandStatus.discovered,
        soldier_name="Красноармеец Иванов И. И.",
        unit="",
        lat=52.5625,
        lon=35.4950,
        circumstances="Место гибели — овраг у д. Крупышино. Требуется подъём.",
        date_text="1943",
        source="ДЕМО по примеру из кейса: Книга Памяти Орловской области, т. 5",
    ),
    LastStandSeed(
        key="vysota-paratroopers",
        status=LastStandStatus.discovered,
        soldier_name="Три неизвестных десантника",
        unit="9-я воздушно-десантная бригада, 5-й ВДК",
        lat=53.1180,
        lon=36.3120,
        circumstances=(
            "Координаты внёс командир отряда «Высота» по итогам экспедиции. "
            "Нужна проверка по архиву и помощь в идентификации."
        ),
        date_text="октябрь 1941",
        source="ДЕМО по сценарию кейса: отчёт отряда «Высота»",
    ),
    LastStandSeed(
        key="mtsensk-tanker",
        status=LastStandStatus.discovered,
        soldier_name="Неизвестный танкист",
        unit="4-я танковая бригада",
        lat=53.2500,
        lon=36.5200,
        circumstances="Со слов местных жителей — место подбитого танка на подступах к Мценску.",
        date_text="октябрь 1941",
        source="ДЕМО: рассказ местных жителей (пример источника)",
    ),
    LastStandSeed(
        key="orel-airfield-paratrooper",
        status=LastStandStatus.archive_confirmed,
        soldier_name="Неизвестный десантник",
        unit="201-я воздушно-десантная бригада, 5-й ВДК",
        lat=52.9210,
        lon=36.0120,
        circumstances="Бой у Орловского аэродрома. Место сверено с донесением о потерях.",
        death_date=date(1941, 10, 3),
        date_text="3 октября 1941",
        source="ДЕМО: пример статуса «Подтверждено архивом»",
    ),
    LastStandSeed(
        key="semenkovo-raised",
        status=LastStandStatus.remains_raised,
        soldier_name="Пятеро бойцов стрелковой роты",
        unit="",
        lat=52.5790,
        lon=35.9600,
        circumstances="Останки подняты отрядом и перезахоронены. Двое бойцов установлены по медальонам.",
        date_text="лето 1943",
        source="ДЕМО: пример отработанной точки",
    ),
)


def seed(db: Session) -> dict[str, int]:
    """Залить демо-точки. Возвращает, сколько строк каждого вида теперь в демо-наборе."""
    for item in POI:
        db.merge(
            PointOfInterest(
                id=seed_id("poi", item.key),
                kind=item.kind,
                title=item.title,
                description=item.description,
                lat=item.lat,
                lon=item.lon,
                event_date=item.event_date,
                date_text=item.date_text,
                source=item.source,
                created_by=SEED_AUTHOR,
            )
        )
    for item in LAST_STAND:
        db.merge(
            LastStandPoint(
                id=seed_id("last-stand", item.key),
                status=item.status,
                soldier_name=item.soldier_name,
                unit=item.unit,
                lat=item.lat,
                lon=item.lon,
                circumstances=item.circumstances,
                death_date=item.death_date,
                date_text=item.date_text,
                source=item.source,
                created_by=SEED_AUTHOR,
            )
        )
    db.commit()
    return {"poi": len(POI), "last_stand": len(LAST_STAND)}


def main() -> None:
    from core.db import SessionLocal, init_db

    init_db()
    with SessionLocal() as db:
        counts = seed(db)
    print(
        f"map_service: слой «ВОВ» — {counts['poi']} точек, «Последний бой» — {counts['last_stand']}"
    )


if __name__ == "__main__":
    main()
