"""
Tests for the activity endpoints (``/activity``).

Activities belong to a minor stage. Validation is stubbed where the test is
about route behavior rather than validation rules.
"""

from helpers import field, raise_error, stub_validation

from app.models import Activity
from db import db

VALIDATE_ACTIVITY = "app.routes.activity_routes.ActivityValidation.validate_activity"


def _activity_payload(name="Boat Tour"):
    """Builds a complete activity form as sent by the frontend."""
    return {
        "name": field(name),
        "description": field("desc"),
        "place": field("Berlin"),
        "costs": field(25),
        "latitude": field(None),
        "longitude": field(None),
        "link": field(""),
        "booked": field(False),
    }


def _create_url(minor_stage_id):
    return f"/activity/create-activity/{minor_stage_id}"


def _update_url(minor_stage_id, activity_id):
    return f"/activity/update-activity/{minor_stage_id}/{activity_id}"


# ---------------------------------------------------------------------------
# POST /activity/create-activity/<minor_stage_id>
# ---------------------------------------------------------------------------


def test_create_activity_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid activity is persisted for the given minor stage."""
    monkeypatch.setattr(VALIDATE_ACTIVITY, stub_validation(True))

    response = client.post(
        _create_url(route_graph_data["minor_stage_id"]),
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(Activity).filter_by(
            name="Boat Tour",
            minor_stage_id=route_graph_data["minor_stage_id"],
        )
    ).scalars().first()
    assert created is not None


def test_create_activity_minor_stage_not_found(client, auth_header, route_graph_data):
    """Creating an activity for an unknown minor stage returns 404."""
    response = client.post(
        _create_url(999999),
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_create_activity_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_ACTIVITY, stub_validation(False))

    response = client.post(
        _create_url(route_graph_data["minor_stage_id"]),
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_activity_lookup_error_returns_400(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected error while loading the parent resources returns 400."""
    monkeypatch.setattr("app.routes.activity_routes.get_user_minor_stage", raise_error)

    response = client.post(
        _create_url(route_graph_data["minor_stage_id"]),
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_activity_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_ACTIVITY, stub_validation(True))
    monkeypatch.setattr("app.routes.activity_routes.db.session.commit", raise_error)

    response = client.post(
        _create_url(route_graph_data["minor_stage_id"]),
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /activity/update-activity/<minor_stage_id>/<activity_id>
# ---------------------------------------------------------------------------


def test_update_activity_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid update is applied to the stored activity."""
    monkeypatch.setattr(VALIDATE_ACTIVITY, stub_validation(True))

    response = client.post(
        _update_url(route_graph_data["minor_stage_id"], route_graph_data["activity_id"]),
        json=_activity_payload("Updated Name"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert response.get_json()["activity"]["name"] == "Updated Name"

    db.session.expire_all()
    assert db.session.get(Activity, route_graph_data["activity_id"]).name == "Updated Name"


def test_update_activity_not_found(client, auth_header, route_graph_data):
    """Updating an unknown activity returns 404."""
    response = client.post(
        _update_url(route_graph_data["minor_stage_id"], 999999),
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_activity_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_ACTIVITY, stub_validation(False))

    response = client.post(
        _update_url(route_graph_data["minor_stage_id"], route_graph_data["activity_id"]),
        json=_activity_payload("Invalid"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_activity_lookup_error_returns_400(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected error while loading the activity returns 400."""
    monkeypatch.setattr("app.routes.activity_routes.get_user_activity", raise_error)

    response = client.post(
        _update_url(route_graph_data["minor_stage_id"], route_graph_data["activity_id"]),
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_activity_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_ACTIVITY, stub_validation(True))
    monkeypatch.setattr("app.routes.activity_routes.db.session.commit", raise_error)

    response = client.post(
        _update_url(route_graph_data["minor_stage_id"], route_graph_data["activity_id"]),
        json=_activity_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /activity/delete-activity/<activity_id>
# ---------------------------------------------------------------------------


def test_delete_activity_success(client, auth_header, route_graph_data):
    """Deleting an own activity removes it from the database."""
    response = client.delete(
        f"/activity/delete-activity/{route_graph_data['activity_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Activity, route_graph_data["activity_id"]) is None


def test_delete_activity_not_found(client, auth_header, route_graph_data):
    """Deleting an unknown activity returns 404."""
    response = client.delete(
        "/activity/delete-activity/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_activity_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr("app.routes.activity_routes.db.session.commit", raise_error)

    response = client.delete(
        f"/activity/delete-activity/{route_graph_data['activity_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
