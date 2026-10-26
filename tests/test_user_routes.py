"""
Tests for the user data endpoint (``/user/get-user-data``).

The endpoint derives the time zone offset and the local currency from
optional coordinates. Without coordinates, or if the lookup fails, it falls
back to defaults (offset 0, EUR).
"""

from helpers import raise_error

ROUTES = "app.routes.user_routes"


def test_get_user_data_without_coordinates_returns_defaults(client, auth_header, route_graph_data):
    """Without coordinates the default offset and currency are returned."""
    response = client.get(
        "/user/get-user-data",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["userId"] == route_graph_data["user_id"]
    assert body["offset"] == 0
    assert body["localCurrency"]["code"] == "EUR"


def test_get_user_data_with_coordinates_uses_location_helpers(client, auth_header, route_graph_data, monkeypatch):
    """With coordinates the offset and currency come from the location helpers."""
    monkeypatch.setattr(f"{ROUTES}.calculate_time_zone_offset", lambda lat, lon: 2)
    monkeypatch.setattr(
        f"{ROUTES}.get_local_currency",
        lambda lat, lon: {"code": "USD", "name": "US Dollar", "symbol": "$", "conversion_rate": 1.1},
    )

    response = client.get(
        "/user/get-user-data?latitude=40.7&longitude=-74.0",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["offset"] == 2
    assert body["localCurrency"]["code"] == "USD"


def test_get_user_data_falls_back_to_defaults_when_location_lookup_fails(
    client, auth_header, route_graph_data, monkeypatch
):
    """A failing location lookup must not break the request; defaults are returned."""
    monkeypatch.setattr(f"{ROUTES}.calculate_time_zone_offset", raise_error)

    response = client.get(
        "/user/get-user-data?latitude=40.7&longitude=-74.0",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert response.get_json()["offset"] == 0
