from app.models import Activity
from db import db


def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _activity_payload(name="Boat Tour"):
    return {
        "name": _field(name),
        "description": _field("desc"),
        "place": _field("Berlin"),
        "costs": _field(25),
        "latitude": _field(None),
        "longitude": _field(None),
        "link": _field(""),
        "booked": _field(False),
    }


def test_create_activity_success(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.activity_routes.ActivityValidation.validate_activity",
        lambda activity: (activity, True),
    )

    response = client.post(
        f"/activity/create-activity/{route_graph_data['minor_stage_id']}",
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(Activity).filter_by(name="Boat Tour", minor_stage_id=route_graph_data["minor_stage_id"])
    ).scalars().first()
    assert created is not None


def test_update_activity_not_found(client, auth_header, route_graph_data):
    response = client.post(
        f"/activity/update-activity/{route_graph_data['minor_stage_id']}/999999",
        json=_activity_payload("X"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code in (400, 404)


def test_delete_activity_success(client, auth_header, route_graph_data):
    response = client.delete(
        f"/activity/delete-activity/{route_graph_data['activity_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_activity_minor_stage_not_found(client, auth_header, route_graph_data):
    response = client.post(
        "/activity/create-activity/999999",
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_create_activity_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = _activity_payload()

    monkeypatch.setattr(
        "app.routes.activity_routes.ActivityValidation.validate_activity",
        lambda activity: (payload, False),
    )

    response = client.post(
        f"/activity/create-activity/{route_graph_data['minor_stage_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_activity_success_with_monkeypatched_resource(client, auth_header, route_graph_data, monkeypatch):
    class _ActivityObj:
        id = 99
        minor_stage_id = 1
        name = "old"
        description = "old"
        place = "old"
        costs = 1
        latitude = None
        longitude = None
        link = ""
        booked = False

    monkeypatch.setattr(
        "app.routes.activity_routes.get_user_activity",
        lambda current_user, activity_id, minor_stage_id=None: _ActivityObj(),
    )
    monkeypatch.setattr(
        "app.routes.activity_routes.ActivityValidation.validate_activity",
        lambda activity: (activity, True),
    )

    response = client.post(
        f"/activity/update-activity/{route_graph_data['minor_stage_id']}/{route_graph_data['activity_id']}",
        json=_activity_payload("Updated Name"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_delete_activity_not_found(client, auth_header, route_graph_data):
    response = client.delete(
        "/activity/delete-activity/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_activity_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = _activity_payload("Invalid")
    monkeypatch.setattr(
        "app.routes.activity_routes.ActivityValidation.validate_activity",
        lambda activity: (payload, False),
    )

    response = client.post(
        f"/activity/update-activity/{route_graph_data['minor_stage_id']}/{route_graph_data['activity_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_update_activity_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routes.activity_routes.get_user_activity",
        _raise,
    )

    response = client.post(
        f"/activity/update-activity/{route_graph_data['minor_stage_id']}/{route_graph_data['activity_id']}",
        json=_activity_payload("Err"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_create_activity_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.activity_routes.get_user_minor_stage",
        lambda current_user, minorStageId: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/activity/create-activity/{route_graph_data['minor_stage_id']}",
        json=_activity_payload("Err create"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_create_activity_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.activity_routes.ActivityValidation.validate_activity",
        lambda activity: (activity, True),
    )
    monkeypatch.setattr(
        "app.routes.activity_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/activity/create-activity/{route_graph_data['minor_stage_id']}",
        json=_activity_payload("Err commit"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_update_activity_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.activity_routes.ActivityValidation.validate_activity",
        lambda activity: (activity, True),
    )
    monkeypatch.setattr(
        "app.routes.activity_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/activity/update-activity/{route_graph_data['minor_stage_id']}/{route_graph_data['activity_id']}",
        json=_activity_payload("Err update"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_delete_activity_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.activity_routes.db.session.commit",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.delete(
        f"/activity/delete-activity/{route_graph_data['activity_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500
