from conftest import auth_header


def published_route_with_waypoints(client, author_header, n=3):
    route = client.post(
        "/routes", headers=author_header, json={"title": "Тропа", "city": "Орёл"}
    ).json()
    wp_ids = []
    for i in range(n):
        w = client.post(
            f"/routes/{route['id']}/waypoints",
            headers=author_header,
            json={"title": f"Точка {i}", "lat": 52.9 + i / 100, "lon": 36.0},
        ).json()
        wp_ids.append(w["id"])
    client.post(
        f"/routes/{route['id']}/publish", headers=author_header, json={"is_published": True}
    )
    return route["id"], wp_ids


def test_start_is_idempotent(client, author_header):
    route_id, _ = published_route_with_waypoints(client, author_header)
    fam = auth_header(user_id="mama-1")
    p1 = client.post(f"/routes/{route_id}/progress/start", headers=fam).json()
    p2 = client.post(f"/routes/{route_id}/progress/start", headers=fam).json()
    assert p1["started_at"] == p2["started_at"]
    assert p1["completed_waypoint_ids"] == []


def test_complete_waypoints_until_done(client, author_header):
    route_id, wp_ids = published_route_with_waypoints(client, author_header, n=3)
    fam = auth_header(user_id="mama-1")

    for i, wid in enumerate(wp_ids, start=1):
        p = client.post(
            f"/routes/{route_id}/progress/complete-waypoint",
            headers=fam,
            json={"waypoint_id": wid},
        ).json()
        assert p["current_index"] == i

    assert p["completed_at"] is not None
    assert p["completed_waypoint_ids"] == wp_ids


def test_complete_keeps_route_order_regardless_of_input_order(client, author_header):
    route_id, wp_ids = published_route_with_waypoints(client, author_header, n=3)
    fam = auth_header(user_id="mama-1")
    for wid in reversed(wp_ids):
        p = client.post(
            f"/routes/{route_id}/progress/complete-waypoint", headers=fam, json={"waypoint_id": wid}
        ).json()
    assert p["completed_waypoint_ids"] == wp_ids


def test_complete_unknown_waypoint_404(client, author_header):
    route_id, _ = published_route_with_waypoints(client, author_header)
    r = client.post(
        f"/routes/{route_id}/progress/complete-waypoint",
        headers=auth_header(user_id="mama-1"),
        json={"waypoint_id": "nope"},
    )
    assert r.status_code == 404


def test_progress_me_before_start_404(client, author_header):
    route_id, _ = published_route_with_waypoints(client, author_header)
    assert (
        client.get(
            f"/routes/{route_id}/progress/me", headers=auth_header(user_id="mama-1")
        ).status_code
        == 404
    )


def test_riddle_answer_is_graded_but_does_not_block_progress(client, author_header):
    route = client.post(
        "/routes", headers=author_header, json={"title": "Тропа", "city": "Орёл"}
    ).json()
    wp = client.post(
        f"/routes/{route['id']}/waypoints",
        headers=author_header,
        json={
            "title": "Пушка",
            "lat": 52.9,
            "lon": 36.0,
            "kid_task": "Найди калибр пушки на иллюстрации",
            "expected_answer": "76 мм",
        },
    ).json()
    # эталонный ответ наружу не отдаётся, только признак, что задание проверяемое.
    assert "expected_answer" not in wp
    assert wp["has_answer"] is True
    client.post(f"/routes/{route['id']}/publish", headers=author_header, json={"is_published": True})

    fam = auth_header(user_id="mama-1")

    wrong = client.post(
        f"/routes/{route['id']}/progress/complete-waypoint",
        headers=fam,
        json={"waypoint_id": wp["id"], "answer": "45 мм"},
    ).json()
    assert wrong["answers"] == {wp["id"]: False}
    # неверный ответ всё равно засчитывает точку как пройденную.
    assert wrong["completed_waypoint_ids"] == [wp["id"]]

    correct = client.post(
        f"/routes/{route['id']}/progress/complete-waypoint",
        headers=fam,
        json={"waypoint_id": wp["id"], "answer": " 76 ММ "},
    ).json()
    assert correct["answers"] == {wp["id"]: True}


def test_completing_route_awards_achievement_once(client, author_header, monkeypatch):
    import services.progress_service as progress_service_module

    calls = []
    monkeypatch.setattr(
        progress_service_module, "award_achievement", lambda **kw: calls.append(kw)
    )

    route_id, wp_ids = published_route_with_waypoints(client, author_header, n=2)
    fam = auth_header(user_id="mama-1")

    client.post(
        f"/routes/{route_id}/progress/complete-waypoint",
        headers=fam,
        json={"waypoint_id": wp_ids[0]},
    )
    assert calls == []  # маршрут ещё не пройден целиком

    client.post(
        f"/routes/{route_id}/progress/complete-waypoint",
        headers=fam,
        json={"waypoint_id": wp_ids[1]},
    )
    assert calls == [{"user_id": "mama-1", "code": "first_route_completed"}]

    # повторная отметка уже пройденной точки не шлёт ачивку ещё раз.
    client.post(
        f"/routes/{route_id}/progress/complete-waypoint",
        headers=fam,
        json={"waypoint_id": wp_ids[1]},
    )
    assert len(calls) == 1


def test_waypoint_without_expected_answer_has_no_answer_flag(client, author_header):
    route_id, wp_ids = published_route_with_waypoints(client, author_header, n=1)
    wps = client.get(f"/routes/{route_id}/waypoints").json()
    assert wps[0]["has_answer"] is False

    fam = auth_header(user_id="mama-1")
    p = client.post(
        f"/routes/{route_id}/progress/complete-waypoint",
        headers=fam,
        json={"waypoint_id": wp_ids[0]},
    ).json()
    assert p["answers"] == {}
