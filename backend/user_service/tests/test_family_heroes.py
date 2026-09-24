from conftest import auth_header


def create_hero(client, header, **over):
    body = {
        "name": "Сержант Воронов А. Г.",
        "status": "killed_in_action",
        "birth_year": 1919,
        "death_year": 1944,
        "unit": "120-й стрелковый полк, Орловский рубеж",
        "note": "Подтверждено в ОБД «Мемориал»",
    }
    body.update(over)
    return client.post("/family-heroes", headers=header, json=body)


def test_create_and_list_own_heroes(client):
    header = auth_header(user_id="u1")
    r = create_hero(client, header)
    assert r.status_code == 201
    body = r.json()
    assert body["owner_id"] == "u1"
    assert body["status"] == "killed_in_action"

    mine = client.get("/family-heroes/mine", headers=header).json()
    assert len(mine) == 1
    assert mine[0]["name"] == "Сержант Воронов А. Г."


def test_create_requires_auth(client):
    r = client.post("/family-heroes", json={"name": "Кто-то"})
    assert r.status_code in (401, 403)


def test_heroes_are_per_owner(client):
    create_hero(client, auth_header(user_id="u1"), name="Герой первого")
    create_hero(client, auth_header(user_id="u2"), name="Герой второго")

    mine1 = client.get("/family-heroes/mine", headers=auth_header(user_id="u1")).json()
    mine2 = client.get("/family-heroes/mine", headers=auth_header(user_id="u2")).json()
    assert [h["name"] for h in mine1] == ["Герой первого"]
    assert [h["name"] for h in mine2] == ["Герой второго"]


def test_update_only_by_owner(client):
    owner = auth_header(user_id="u1")
    hero = create_hero(client, owner).json()

    stranger = auth_header(user_id="u2")
    forbidden = client.patch(
        f"/family-heroes/{hero['id']}", headers=stranger, json={"note": "чужая правка"}
    )
    assert forbidden.status_code == 403

    ok = client.patch(
        f"/family-heroes/{hero['id']}", headers=owner, json={"note": "уточнённая заметка"}
    )
    assert ok.status_code == 200
    assert ok.json()["note"] == "уточнённая заметка"


def test_root_can_update_others_hero(client):
    owner = auth_header(user_id="u1")
    hero = create_hero(client, owner).json()

    root = auth_header(user_id="root-1", is_root=True)
    r = client.patch(f"/family-heroes/{hero['id']}", headers=root, json={"note": "модерация"})
    assert r.status_code == 200


def test_birth_year_can_be_cleared(client):
    owner = auth_header(user_id="u1")
    hero = create_hero(client, owner).json()
    assert hero["birth_year"] == 1919

    cleared = client.patch(
        f"/family-heroes/{hero['id']}", headers=owner, json={"birth_year": None}
    )
    assert cleared.status_code == 200
    assert cleared.json()["birth_year"] is None


def test_name_ignores_explicit_null(client):
    owner = auth_header(user_id="u1")
    hero = create_hero(client, owner).json()

    r = client.patch(f"/family-heroes/{hero['id']}", headers=owner, json={"name": None})
    assert r.status_code == 200
    assert r.json()["name"] == hero["name"]


def test_delete_only_by_owner(client):
    owner = auth_header(user_id="u1")
    hero = create_hero(client, owner).json()

    stranger = auth_header(user_id="u2")
    assert client.delete(f"/family-heroes/{hero['id']}", headers=stranger).status_code == 403

    assert client.delete(f"/family-heroes/{hero['id']}", headers=owner).status_code == 204
    assert client.get("/family-heroes/mine", headers=owner).json() == []


def test_update_unknown_hero_404(client):
    owner = auth_header(user_id="u1")
    r = client.patch("/family-heroes/does-not-exist", headers=owner, json={"note": "x"})
    assert r.status_code == 404


def test_heroes_visible_on_own_and_public_profile(client):
    owner = auth_header(user_id="u1")
    client.get("/profiles/me", headers=owner)  # ленивое создание профиля

    create_hero(client, owner)

    mine = client.get("/profiles/me", headers=owner).json()
    assert len(mine["heroes"]) == 1
    assert mine["heroes"][0]["name"] == "Сержант Воронов А. Г."

    stranger_view = client.get("/profiles/u1", headers=auth_header(user_id="stranger")).json()
    assert len(stranger_view["heroes"]) == 1


def test_profile_without_heroes_has_empty_list(client):
    header = auth_header(user_id="u2")
    profile = client.get("/profiles/me", headers=header).json()
    assert profile["heroes"] == []
