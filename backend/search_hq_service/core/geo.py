import math

EARTH_RADIUS_M = 6_371_000.0


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние по поверхности Земли (гаверсинус), в метрах — та же формула, что в map_service."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    h = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))
