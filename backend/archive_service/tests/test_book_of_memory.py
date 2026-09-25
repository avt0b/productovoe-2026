"""Книга памяти: алфавит, листание и сводку считает сервер — карточек десятки тысяч."""

from conftest import auth_header

HISTORIAN = auth_header(user_id="historian-1", role="local_historian")


def add_card(client, title, **over):
    body = {"kind": "soldier_card", "title": title, "body": "Погиб в 1943 году."}
    body.update(over)
    created = client.post("/entries", headers=auth_header(user_id="author-1"), json=body)
    assert created.status_code == 201
    entry = created.json()
    verified = client.post(f"/entries/{entry['id']}/verify", headers=HISTORIAN, json={})
    assert verified.status_code == 200
    return entry


def titles(client, **params):
    response = client.get("/entries", params={"kind": "soldier_card", **params})
    assert response.status_code == 200
    return [entry["title"] for entry in response.json()]


def test_cards_are_listed_alphabetically_page_by_page(client):
    for title in ("Бобров Иван", "Абрамов Пётр", "Вешкин Семён", "Абашев Юнус"):
        add_card(client, title)

    assert titles(client, sort="title") == [
        "Абашев Юнус",
        "Абрамов Пётр",
        "Бобров Иван",
        "Вешкин Семён",
    ]
    assert titles(client, sort="title", limit=2, offset=2) == ["Бобров Иван", "Вешкин Семён"]


def test_letter_filters_by_start_of_title(client):
    for title in ("Бобров Иван", "Абрамов Пётр", "Вешкин Семён", "Абашев Юнус"):
        add_card(client, title)

    assert titles(client, sort="title", prefix="А") == ["Абашев Юнус", "Абрамов Пётр"]
    assert titles(client, sort="title", prefix="Абр") == ["Абрамов Пётр"]


def test_prefix_is_text_not_a_pattern(client):
    add_card(client, "Абашев Юнус")

    assert titles(client, prefix="%") == []
    assert titles(client, prefix="_") == []


def test_summary_counts_verified_cards_of_the_section(client):
    add_card(client, "Бобров Иван", date_text="1905 — 13.07.1943", lat=53.0, lon=36.0)
    add_card(client, "Абрамов Пётр")
    # Не подтверждена — в Книге памяти её ещё нет.
    client.post(
        "/entries",
        headers=auth_header(user_id="author-1"),
        json={"kind": "soldier_card", "title": "Воронов Алексей"},
    )
    # Другой раздел архива в сводку бойцов не попадает.
    add_card(client, "Письмо с фронта", kind="memory")

    summary = client.get("/entries/summary", params={"kind": "soldier_card"})
    assert summary.status_code == 200
    assert summary.json() == {"total": 2, "with_date": 1, "on_map": 1, "letters": ["А", "Б"]}


def test_summary_route_is_not_taken_for_entry_id(client):
    assert client.get("/entries/summary").status_code == 200


def test_search_puts_surname_matches_before_text_matches(client):
    add_card(client, "Алексеев Иван", body="Похоронен у деревни Жуково.")
    add_card(client, "Жуков Пётр")

    assert titles(client, sort="title", q="Жуков") == ["Жуков Пётр", "Алексеев Иван"]


def test_alphabet_has_only_letters(client):
    add_card(client, "[неизвестно] Алексей Никифорович")
    add_card(client, "Бобров Иван")

    assert client.get("/entries/summary", params={"kind": "soldier_card"}).json()["letters"] == [
        "Б"
    ]


def test_unknown_surnames_go_after_the_alphabet(client):
    add_card(client, "[неизвестно] Алексей Никифорович")
    add_card(client, "Бобров Иван")
    add_card(client, "Абрамов Пётр")

    assert titles(client, sort="title") == [
        "Абрамов Пётр",
        "Бобров Иван",
        "[неизвестно] Алексей Никифорович",
    ]
