"""Клиенты user_service: семья и профили. user_service лежит — сервис не падает."""

import httpx

# Настоящие функции, взятые до подмены заглушками из conftest.
from services.family_client import family_member_ids as real_family_member_ids
from services.profile_client import profile_briefs as real_profile_briefs


def down(*args, **kwargs):
    raise httpx.ConnectError("user_service лежит")


def test_family_client_returns_ids_and_survives_outage(monkeypatch):
    seen = {}

    def answer(url, *, headers, timeout):
        seen["url"], seen["key"] = url, headers["X-Internal-Key"]
        return httpx.Response(
            200, json={"user_id": "kid", "member_ids": ["mom", "dad"]}, request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx, "get", answer)
    assert real_family_member_ids("kid") == ["mom", "dad"]
    assert seen["url"].endswith("/internal/family/kid")
    assert seen["key"]

    monkeypatch.setattr(httpx, "get", down)
    assert real_family_member_ids("kid") == []


def test_profile_client_asks_in_chunks_of_200_and_survives_outage(monkeypatch):
    asked = []

    def answer(url, *, params, timeout):
        ids = params["ids"].split(",")
        asked.append(len(ids))
        cards = [
            {"id": uid, "display_name": " Имя ", "avatar_url": None, "city": "Орёл", "role": "family", "is_verified": False}
            for uid in ids
        ]
        return httpx.Response(200, json=cards, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", answer)
    ids = [f"user-{n}" for n in range(250)]
    briefs = real_profile_briefs([*ids, "user-0", ""])
    assert asked == [200, 50]
    assert len(briefs) == 250
    assert briefs["user-7"].display_name == "Имя"
    assert briefs["user-7"].city == "Орёл"

    monkeypatch.setattr(httpx, "get", down)
    assert real_profile_briefs(["user-1"]) == {}
