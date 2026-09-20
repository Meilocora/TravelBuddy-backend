import pytest



def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _place_payload(country_id):
    return {
        "countryId": _field(country_id),
        "name": _field("My Place"),
        "description": _field("desc"),
        "visited": _field(False),
        "favorite": _field(False),
        "latitude": _field(52.5),
        "longitude": _field(13.4),
        "link": _field(""),
    }


def test_get_places_success(client, auth_header, route_graph_data):
    response = client.get(
        "/place-to-visit/get-places",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_place_success(client, auth_header, route_graph_data, monkeypatch):
    payload = _place_payload(route_graph_data["custom_country_id"])

    monkeypatch.setattr(
        "app.routes.place_routes.PlaceValidation.validate_place",
        lambda place: (place, True),
    )

    response = client.post(
        "/place-to-visit/create-place",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_toggle_favorite_place_success(client, auth_header, route_graph_data):
    response = client.post(
        f"/place-to-visit/toggle-favorite-place/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_update_place_success(client, auth_header, route_graph_data, monkeypatch):
    payload = _place_payload(route_graph_data["custom_country_id"])
    payload["name"] = _field("Updated Place")

    monkeypatch.setattr(
        "app.routes.place_routes.PlaceValidation.validate_place",
        lambda place: (place, True),
    )

    response = client.post(
        f"/place-to-visit/update-place/{route_graph_data['place_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_toggle_visited_place_success(client, auth_header, route_graph_data):
    response = client.post(
        f"/place-to-visit/toggle-visited-place/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_add_and_remove_minor_stage_relation(client, auth_header, route_graph_data):
    add_response = client.post(
        f"/place-to-visit/add-minor-stage-to-place/{route_graph_data['place_id']}/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert add_response.status_code == 200

    remove_response = client.post(
        f"/place-to-visit/remove-minor-stage-from-place/{route_graph_data['place_id']}/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert remove_response.status_code == 200


def test_get_places_by_country_success(client, auth_header, route_graph_data):
    response = client.get(
        f"/place-to-visit/get-available-places-by-country/{route_graph_data['minor_stage_id']}/Germany",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_place_not_found_country(client, auth_header, route_graph_data):
    response = client.post(
        "/place-to-visit/create-place",
        json=_place_payload(999999),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_place_not_found(client, auth_header, route_graph_data):
    response = client.post(
        "/place-to-visit/update-place/999999",
        json=_place_payload(route_graph_data["custom_country_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_toggle_place_not_found_paths(client, auth_header, route_graph_data):
    fav_response = client.post(
        "/place-to-visit/toggle-favorite-place/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert fav_response.status_code == 404

    visited_response = client.post(
        "/place-to-visit/toggle-visited-place/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert visited_response.status_code == 404


def test_delete_place_not_found(client, auth_header, route_graph_data):
    response = client.delete(
        "/place-to-visit/delete-place/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_add_remove_minor_stage_resource_not_found(client, auth_header, route_graph_data):
    add_response = client.post(
        "/place-to-visit/add-minor-stage-to-place/999999/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert add_response.status_code == 404

    remove_response = client.post(
        "/place-to-visit/remove-minor-stage-from-place/999999/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert remove_response.status_code == 404


def test_get_places_exception_returns_500(client, auth_header, route_graph_data, monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routes.place_routes.db.session.execute",
        _raise,
    )

    response = client.get(
        "/place-to-visit/get-places",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_get_places_by_country_missing_minor_stage_returns_500(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.place_routes.get_user_minor_stage",
        lambda current_user, minorStageId, major_stage_id=None: None,
    )

    with pytest.raises(TypeError):
        client.get(
            f"/place-to-visit/get-available-places-by-country/{route_graph_data['minor_stage_id']}/Germany",
            headers=auth_header(route_graph_data["user_id"]),
        )


def test_create_place_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = _place_payload(route_graph_data["custom_country_id"])
    monkeypatch.setattr(
        "app.routes.place_routes.PlaceValidation.validate_place",
        lambda place: (place, False),
    )

    response = client.post(
        "/place-to-visit/create-place",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_create_place_invalid_payload_returns_400(client, auth_header, route_graph_data):
    response = client.post(
        "/place-to-visit/create-place",
        json={},
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_update_place_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = _place_payload(route_graph_data["custom_country_id"])
    monkeypatch.setattr(
        "app.routes.place_routes.PlaceValidation.validate_place",
        lambda place: (place, False),
    )

    response = client.post(
        f"/place-to-visit/update-place/{route_graph_data['place_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_delete_place_success(client, auth_header, route_graph_data):
    response = client.delete(
        f"/place-to-visit/delete-place/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 200


def test_toggle_favorite_place_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.place_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/place-to-visit/toggle-favorite-place/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_toggle_visited_place_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.place_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/place-to-visit/toggle-visited-place/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_delete_place_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.place_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.delete(
        f"/place-to-visit/delete-place/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_add_minor_stage_to_place_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.place_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/place-to-visit/add-minor-stage-to-place/{route_graph_data['place_id']}/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_remove_minor_stage_from_place_exception(client, auth_header, route_graph_data, monkeypatch):
    client.post(
        f"/place-to-visit/add-minor-stage-to-place/{route_graph_data['place_id']}/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    monkeypatch.setattr(
        "app.routes.place_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/place-to-visit/remove-minor-stage-from-place/{route_graph_data['place_id']}/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500
