"""Гео-хелпер без PostGIS — тот же приём, что в map_service/core/geo.py."""

import math

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bbox_covering(
    points: list[tuple[float, float]], padding_km: float
) -> tuple[float, float, float, float]:
    """Прямоугольник вокруг всех точек маршрута с запасом в padding_km по краям."""
    lats = [lat for lat, _ in points]
    lons = [lon for _, lon in points]
    mean_lat = sum(lats) / len(lats)
    dlat = padding_km / 111.0
    cos_lat = max(math.cos(math.radians(mean_lat)), 1e-6)
    dlon = padding_km / (111.0 * cos_lat)
    return (min(lats) - dlat, min(lons) - dlon, max(lats) + dlat, max(lons) + dlon)
