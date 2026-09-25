import pytest
from test_progress import published_route_with_waypoints


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


def test_publishing_a_route_credits_its_author(client, author_header, awarded):
    route_id, _ = published_route_with_waypoints(client, author_header)
    assert [code for _, code in awarded] == ["historian_route_author"]

    # Снять с публикации — значка за это нет.
    client.post(f"/routes/{route_id}/publish", headers=author_header, json={"is_published": False})
    assert len(awarded) == 1
