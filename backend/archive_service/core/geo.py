"""Радиус-поиск: грубая рамка в SQL плюс точный haversine в Python.

Тот же приём, что в `map_service/core/geo.py`, — повторён здесь намеренно:
сервисы независимы и общей библиотеки у них нет. PostGIS в archive_service не
поднимаем: записей архива на порядок меньше, чем точек карты, и рамка с
досчётом в Python на этих объёмах не узкое место.
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
    """Рамка (min_lat, min_lon, max_lat, max_lon) вокруг точки — чуть шире круга.

    Долгота растягивается по широте: на широте Орла градус долготы почти вдвое
    короче градуса широты, и рамка без поправки вышла бы полоской.
    """
    dlat = radius_km / 111.0
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)
    dlon = radius_km / (111.0 * cos_lat)
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)
