

def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _medium_payload(minor_stage_id=None, place_id=None):
    return {
        "mediumType": "image",
        "url": _field("https://example.com/new.jpg"),
        "thumbnailUrl": None,
        "favorite": _field(False),
        "latitude": _field(None),
        "longitude": _field(None),
        "timestamp": _field("01.09.2026 10:00"),
        "description": _field("new"),
        "duration": _field(None),
        "minorStageId": _field(minor_stage_id),
        "placeToVisitId": _field(place_id),
        "storageType": "local",
        "assetId": _field("asset-2"),
    }


def test_get_media_success(client, auth_header, route_graph_data):
    response = client.get(
        "/medium/get-media/local",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "media" in response.get_json()


def test_add_medium_success(client, auth_header, route_graph_data):
    response = client.post(
        "/medium/add-medium",
        json=_medium_payload(route_graph_data["minor_stage_id"], route_graph_data["place_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_delete_media_invalid_payload(client, auth_header, route_graph_data):
    response = client.delete(
        "/medium/delete-media",
        json={"ids": []},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_get_media_error_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.medium_routes.fetch_media",
        lambda current_user, storage_type: Exception("boom"),
    )

    response = client.get(
        "/medium/get-media/local",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_add_medium_minor_not_found(client, auth_header, route_graph_data):
    response = client.post(
        "/medium/add-medium",
        json=_medium_payload(999999, route_graph_data["place_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_medium_success(client, auth_header, route_graph_data):
    response = client.post(
        f"/medium/update-medium/{route_graph_data['medium_id']}",
        json=_medium_payload(route_graph_data["minor_stage_id"], route_graph_data["place_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_update_medium_place_not_found(client, auth_header, route_graph_data):
    response = client.post(
        f"/medium/update-medium/{route_graph_data['medium_id']}",
        json=_medium_payload(route_graph_data["minor_stage_id"], 999999),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_medium_success(client, auth_header, route_graph_data):
    response = client.delete(
        f"/medium/delete-medium/{route_graph_data['medium_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_delete_media_bulk_success(client, auth_header, route_graph_data):
    response = client.delete(
        "/medium/delete-media",
        json=[route_graph_data["medium_id"]],
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_delete_media_bulk_not_found(client, auth_header, route_graph_data):
    response = client.delete(
        "/medium/delete-media",
        json=[999999],
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_add_medium_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.medium_routes.get_user_minor_stage",
        lambda current_user, stage_id: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        "/medium/add-medium",
        json=_medium_payload(route_graph_data["minor_stage_id"], route_graph_data["place_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_add_medium_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.medium_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        "/medium/add-medium",
        json=_medium_payload(route_graph_data["minor_stage_id"], route_graph_data["place_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_update_medium_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.medium_routes.get_user_medium",
        lambda current_user, mediumId: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/medium/update-medium/{route_graph_data['medium_id']}",
        json=_medium_payload(route_graph_data["minor_stage_id"], route_graph_data["place_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_update_medium_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.medium_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/medium/update-medium/{route_graph_data['medium_id']}",
        json=_medium_payload(route_graph_data["minor_stage_id"], route_graph_data["place_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_delete_medium_not_found(client, auth_header, route_graph_data):
    response = client.delete(
        "/medium/delete-medium/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 404


def test_delete_media_bulk_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.medium_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.delete(
        "/medium/delete-media",
        json=[route_graph_data["medium_id"]],
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500
