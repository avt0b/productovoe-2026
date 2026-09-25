import pytest

import services.media_prompt_service as media_prompt_service_module

WAYPOINT_A = {"lat": 52.9686, "lon": 36.0694}


def make_route(client, header, **over):
    body = {"title": "Тропа памяти: Орёл", "mode": "family", "city": "Орёл"}
    body.update(over)
    return client.post("/routes", headers=header, json=body).json()


def add_wp(client, header, route_id, **over):
    body = {"title": "Братская могила", "story": "", "kid_task": "", **WAYPOINT_A}
    body.update(over)
    return client.post(f"/routes/{route_id}/waypoints", headers=header, json=body).json()


def publish(client, header, route_id):
    client.post(f"/routes/{route_id}/publish", headers=header, json={"is_published": True})


@pytest.fixture()
def fake_media(monkeypatch):
    """Подменяет поход в media_service: тест сам решает, есть ли уже клип у точки."""
    calls = []

    async def fake_has_clip(poi_id):
        calls.append(poi_id)
        return poi_id in fake_has_clip.with_clip

    fake_has_clip.with_clip = set()
    monkeypatch.setattr(media_prompt_service_module, "has_public_clip", fake_has_clip)
    fake_has_clip.calls = calls
    return fake_has_clip


def test_waypoint_without_clip_is_prompted(client, author_header, fake_media):
    route = make_route(client, author_header)
    wp = add_wp(client, author_header, route["id"], poi_id="poi-1")
    publish(client, author_header, route["id"])

    r = client.get(f"/routes/{route['id']}/media-prompts")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0] == {"waypoint_id": wp["id"], "poi_id": "poi-1", "title": "Братская могила"}


def test_waypoint_with_existing_clip_is_not_prompted(client, author_header, fake_media):
    route = make_route(client, author_header)
    add_wp(client, author_header, route["id"], poi_id="poi-1")
    publish(client, author_header, route["id"])
    fake_media.with_clip = {"poi-1"}

    assert client.get(f"/routes/{route['id']}/media-prompts").json() == []


def test_waypoint_without_poi_id_is_skipped(client, author_header, fake_media):
    route = make_route(client, author_header)
    add_wp(client, author_header, route["id"], poi_id=None)
    publish(client, author_header, route["id"])

    assert client.get(f"/routes/{route['id']}/media-prompts").json() == []
    assert fake_media.calls == []


def test_draft_route_prompts_hidden_from_strangers(client, author_header, fake_media):
    route = make_route(client, author_header)
    add_wp(client, author_header, route["id"], poi_id="poi-1")
    # не публикуем

    assert client.get(f"/routes/{route['id']}/media-prompts").status_code == 404
    assert (
        client.get(f"/routes/{route['id']}/media-prompts", headers=author_header).status_code
        == 200
    )
