"""Python-фолбэк геопоиска: bbox-фильтр + haversine.

На Postgres реальный радиус-поиск идёт через PostGIS (geography(Point),
GiST-индекс, ST_DWithin) — см. core/db._ensure_postgis и
repositories/*.nearby_postgis. Этот модуль остаётся рабочим путём для sqlite
(весь тестовый набор) и любой БД без PostGIS — сервисы сами выбирают, куда
идти, по core.db.engine.dialect.name.
"""

import math

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bbox_around(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Грубая рамка (min_lat, min_lon, max_lat, max_lon) вокруг точки.

    Чуть шире круга — используется как предфильтр в SQL, точный радиус
    проверяется haversine уже в Python.
    """
    dlat = radius_km / 111.0
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)
    dlon = radius_km / (111.0 * cos_lat)
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)
