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
    client.post(f"/routes/{route['id']}/publish", headers=author_header, json={"is_published": True})
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
    assert client.get(
        f"/routes/{route_id}/progress/me", headers=auth_header(user_id="mama-1")
    ).status_code == 404
