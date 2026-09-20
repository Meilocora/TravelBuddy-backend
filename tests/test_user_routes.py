def test_get_user_data_without_coordinates_returns_defaults(
    client,
    auth_header,
    route_graph_data,
):
    response = client.get(
        "/user/get-user-data",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["userId"] == route_graph_data["user_id"]
    assert body["offset"] == 0
    assert body["localCurrency"]["code"] == "EUR"


def test_get_user_data_with_coordinates_uses_helpers(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.user_routes.calculate_time_zone_offset",
        lambda lat, lon: 2,
    )
    monkeypatch.setattr(
        "app.routes.user_routes.get_local_currency",
        lambda lat, lon: {
            "code": "USD",
            "name": "US Dollar",
            "symbol": "$",
            "conversion_rate": 1.1,
        },
    )

    response = client.get(
        "/user/get-user-data?latitude=40.7&longitude=-74.0",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["offset"] == 2
    assert body["localCurrency"]["code"] == "USD"


def test_get_user_data_with_coordinates_handles_helper_exception(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    def _raise(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routes.user_routes.calculate_time_zone_offset",
        _raise,
    )

    response = client.get(
        "/user/get-user-data?latitude=40.7&longitude=-74.0",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["offset"] == 0
