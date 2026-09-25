import pytest
from conftest import auth_header

FINDER = auth_header(user_id="finder-1", role="searcher")
HISTORIAN = auth_header(user_id="historian-1", role="local_historian")
ROOT = auth_header(user_id="root-1", is_root=True)


@pytest.fixture()
def awarded(monkeypatch):
    import services.achievement_client as achievement_client_module

    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        achievement_client_module,
        "award_achievement",
        lambda *, user_id, code: calls.append((user_id, code)),
    )
    return calls


def test_find_and_its_stages_credit_the_finder(client, awarded):
    point = client.post(
        "/last-stand", headers=FINDER, json={"soldier_name": "Иванов И.И.", "lat": 52.74, "lon": 35.97}
    ).json()
    assert ("finder-1", "searcher_first_find") in awarded

    client.patch(f"/last-stand/{point['id']}/status", headers=ROOT, json={"status": "archive_confirmed"})
    client.patch(f"/last-stand/{point['id']}/status", headers=ROOT, json={"status": "remains_raised"})
    # Значки — нашедшему, а не администратору, который сменил стадию.
    assert ("finder-1", "searcher_archive_confirmed") in awarded
    assert ("finder-1", "searcher_remains_raised") in awarded
    assert not any(user == "root-1" for user, _ in awarded)


def test_poi_author_badge(client, awarded):
    client.post(
        "/poi",
        headers=HISTORIAN,
        json={"kind": "monument", "title": "Обелиск", "lat": 52.97, "lon": 36.07},
    )
    assert ("historian-1", "historian_poi_author") in awarded
