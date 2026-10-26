"""
Tests for the media endpoints (``/medium``).

A medium (image/video) belongs to a user and can optionally be linked to a
minor stage and/or a place to visit.
"""

from helpers import field, raise_error

from app.models import Medium
from db import db

ROUTES = "app.routes.medium_routes"


def _medium_payload(minor_stage_id=None, place_id=None):
    """Builds a medium form; ``mediumType`` and ``storageType`` are sent as plain values."""
    return {
        "mediumType": "image",
        "url": field("https://example.com/new.jpg"),
        "thumbnailUrl": None,
        "favorite": field(False),
        "latitude": field(None),
        "longitude": field(None),
        "timestamp": field("01.09.2026 10:00"),
        "description": field("new"),
        "duration": field(None),
        "minorStageId": field(minor_stage_id),
        "placeToVisitId": field(place_id),
        "storageType": "local",
        "assetId": field("asset-2"),
    }


def _linked_payload(route_graph_data):
    """Medium form linked to the fixture's minor stage and place."""
    return _medium_payload(route_graph_data["minor_stage_id"], route_graph_data["place_id"])


# ---------------------------------------------------------------------------
# GET /medium/get-media/<storage_type>
# ---------------------------------------------------------------------------


def test_get_media_success(client, auth_header, route_graph_data):
    """The user's media for the given storage type are returned."""
    response = client.get(
        "/medium/get-media/local",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "media" in response.get_json()


def test_get_media_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """``fetch_media`` signals failures by returning an Exception; the route maps it to 500."""
    monkeypatch.setattr(f"{ROUTES}.fetch_media", lambda *args, **kwargs: Exception("Simulated failure"))

    response = client.get(
        "/medium/get-media/local",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /medium/add-medium
# ---------------------------------------------------------------------------


def test_add_medium_success(client, auth_header, route_graph_data):
    """A medium linked to an own minor stage and place is created."""
    response = client.post(
        "/medium/add-medium",
        json=_linked_payload(route_graph_data),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(Medium).filter_by(asset_id="asset-2", user_id=route_graph_data["user_id"])
    ).scalar_one_or_none()
    assert created is not None


def test_add_medium_minor_stage_not_found(client, auth_header, route_graph_data):
    """Linking a new medium to an unknown minor stage returns 404."""
    response = client.post(
        "/medium/add-medium",
        json=_medium_payload(999999, route_graph_data["place_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_add_medium_lookup_error_returns_400(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected error while loading the linked minor stage returns 400."""
    monkeypatch.setattr(f"{ROUTES}.get_user_minor_stage", raise_error)

    response = client.post(
        "/medium/add-medium",
        json=_linked_payload(route_graph_data),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_add_medium_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        "/medium/add-medium",
        json=_linked_payload(route_graph_data),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /medium/update-medium/<medium_id>
# ---------------------------------------------------------------------------


def test_update_medium_success(client, auth_header, route_graph_data):
    """A valid update is applied to the stored medium."""
    response = client.post(
        f"/medium/update-medium/{route_graph_data['medium_id']}",
        json=_linked_payload(route_graph_data),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Medium, route_graph_data["medium_id"]).description == "new"


def test_update_medium_place_not_found(client, auth_header, route_graph_data):
    """Linking a medium to an unknown place returns 404."""
    response = client.post(
        f"/medium/update-medium/{route_graph_data['medium_id']}",
        json=_medium_payload(route_graph_data["minor_stage_id"], 999999),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_medium_lookup_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected error while loading the medium is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.get_user_medium", raise_error)

    response = client.post(
        f"/medium/update-medium/{route_graph_data['medium_id']}",
        json=_linked_payload(route_graph_data),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_medium_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        f"/medium/update-medium/{route_graph_data['medium_id']}",
        json=_linked_payload(route_graph_data),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /medium/delete-medium/<medium_id>
# ---------------------------------------------------------------------------


def test_delete_medium_success(client, auth_header, route_graph_data):
    """Deleting an own medium removes it."""
    response = client.delete(
        f"/medium/delete-medium/{route_graph_data['medium_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Medium, route_graph_data["medium_id"]) is None


def test_delete_medium_not_found(client, auth_header, route_graph_data):
    """Deleting an unknown medium returns 404."""
    response = client.delete(
        "/medium/delete-medium/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /medium/delete-media (bulk delete, body: list of ids)
# ---------------------------------------------------------------------------


def test_delete_media_bulk_success(client, auth_header, route_graph_data):
    """All listed media are deleted."""
    response = client.delete(
        "/medium/delete-media",
        json=[route_graph_data["medium_id"]],
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Medium, route_graph_data["medium_id"]) is None


def test_delete_media_bulk_invalid_payload(client, auth_header, route_graph_data):
    """A body that is not a list of ids is rejected with 400."""
    response = client.delete(
        "/medium/delete-media",
        json={"ids": []},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_delete_media_bulk_not_found(client, auth_header, route_graph_data):
    """A bulk delete containing an unknown id returns 404."""
    response = client.delete(
        "/medium/delete-media",
        json=[999999],
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_media_bulk_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.delete(
        "/medium/delete-media",
        json=[route_graph_data["medium_id"]],
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
