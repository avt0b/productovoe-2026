import pytest
from conftest import auth_header

HISTORIAN = auth_header(user_id="historian-1", role="local_historian")


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


def test_archive_keeper_after_ten_verified_entries(client, awarded):
    for n in range(10):
        entry = client.post(
            "/entries", headers=auth_header(user_id=f"author-{n}"), json={"kind": "memory", "title": f"Запись {n}"}
        ).json()
        client.post(f"/entries/{entry['id']}/verify", headers=HISTORIAN, json={})
        if n < 9:
            assert ("historian-1", "historian_archive_keeper") not in awarded
    assert ("historian-1", "historian_archive_keeper") in awarded


def test_rejected_entries_do_not_count(client, awarded):
    for n in range(10):
        entry = client.post(
            "/entries", headers=auth_header(user_id=f"author-{n}"), json={"kind": "memory", "title": f"Запись {n}"}
        ).json()
        client.post(f"/entries/{entry['id']}/reject", headers=HISTORIAN, json={})
    assert ("historian-1", "historian_archive_keeper") not in awarded
