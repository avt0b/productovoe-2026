from datetime import UTC, datetime, timedelta

from conftest import auth_header

SITE = {"lat": 52.967986, "lon": 36.078488}
GUIDE = auth_header(user_id="guide-1", role="local_historian")

STOPS = [
    {"name": "Вечный огонь", "lat": 52.9686, "lon": 36.0694, "note": "Минута молчания"},
    {"name": "Танк Т-34-85", "lat": 52.9701, "lon": 36.0612, "poi_id": "poi-tank"},
    {"name": "Памятник артиллеристам", "lat": 52.9655, "lon": 36.0801},
]


def body(**over):
    data = {
        "title": "Тропа памяти",
        "place_name": "Площадь Мира",
        "starts_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "capacity": 10,
        **SITE,
    }
    data.update(over)
    return data


def test_excursion_keeps_route_in_order(client):
    r = client.post("/excursions", headers=GUIDE, json=body(stops=STOPS))
    assert r.status_code == 201
    stops = r.json()["stops"]
    assert [s["name"] for s in stops] == ["Вечный огонь", "Танк Т-34-85", "Памятник артиллеристам"]
    assert [s["position"] for s in stops] == [0, 1, 2]
    assert stops[0]["note"] == "Минута молчания"
    assert stops[1]["poi_id"] == "poi-tank"

    # В списке экскурсий маршрут тоже есть.
    listed = client.get("/excursions").json()
    assert [s["name"] for s in listed[0]["stops"]] == [s["name"] for s in STOPS]


def test_route_is_replaced_only_when_sent(client):
    excursion = client.post("/excursions", headers=GUIDE, json=body(stops=STOPS)).json()
    path = f"/excursions/{excursion['id']}"

    kept = client.patch(path, headers=GUIDE, json={"title": "Новое название"}).json()
    assert len(kept["stops"]) == 3

    reordered = client.patch(path, headers=GUIDE, json={"stops": [STOPS[2], STOPS[0]]}).json()
    assert [s["name"] for s in reordered["stops"]] == ["Памятник артиллеристам", "Вечный огонь"]

    cleared = client.patch(path, headers=GUIDE, json={"stops": []}).json()
    assert cleared["stops"] == []


def test_excursion_cannot_start_in_the_past(client):
    yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    r = client.post("/excursions", headers=GUIDE, json=body(starts_at=yesterday))
    assert r.status_code == 409

    # «Прямо сейчас» — можно: часы телефона могут отставать на пару минут.
    just_now = (datetime.now(UTC) - timedelta(minutes=2)).isoformat()
    assert client.post("/excursions", headers=GUIDE, json=body(starts_at=just_now)).status_code == 201

    excursion = client.post("/excursions", headers=GUIDE, json=body()).json()
    moved = client.patch(f"/excursions/{excursion['id']}", headers=GUIDE, json={"starts_at": yesterday})
    assert moved.status_code == 409


def test_too_long_route_is_rejected(client):
    stops = [{"name": f"Точка {n}", **SITE} for n in range(21)]
    assert client.post("/excursions", headers=GUIDE, json=body(stops=stops)).status_code == 422
