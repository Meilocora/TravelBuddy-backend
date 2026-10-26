"""
Tests for the places-to-visit endpoints (``/place-to-visit``).

A place belongs to one of the user's custom countries and can be linked to
minor stages. Validation is stubbed where the test is about route behavior.
"""

import pytest
from helpers import field, raise_error, stub_validation

from app.models import PlaceToVisit
from db import db

ROUTES = "app.routes.place_routes"
VALIDATE_PLACE = f"{ROUTES}.PlaceValidation.validate_place"


def _place_payload(country_id, name="My Place"):
    """Builds a complete place form for the given custom country."""
    return {
        "countryId": field(country_id),
        "name": field(name),
        "description": field("desc"),
        "visited": field(False),
        "favorite": field(False),
        "latitude": field(52.5),
        "longitude": field(13.4),
        "link": field(""),
    }


def _link_url(action, place_id, minor_stage_id):
    """URL for linking (``add``) or unlinking (``remove``) a place and a minor stage."""
    path = "add-minor-stage-to-place" if action == "add" else "remove-minor-stage-from-place"
    return f"/place-to-visit/{path}/{place_id}/{minor_stage_id}"


# ---------------------------------------------------------------------------
# GET /place-to-visit/get-places
# ---------------------------------------------------------------------------


def test_get_places_success(client, auth_header, route_graph_data):
    """The user's places are returned."""
    response = client.get(
        "/place-to-visit/get-places",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_get_places_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database query is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.execute", raise_error)

    response = client.get(
        "/place-to-visit/get-places",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /place-to-visit/get-available-places-by-country/<minor_stage_id>/<country>
# ---------------------------------------------------------------------------


def test_get_places_by_country_success(client, auth_header, route_graph_data):
    """Places of the given country that can be linked to the minor stage are returned."""
    response = client.get(
        f"/place-to-visit/get-available-places-by-country/{route_graph_data['minor_stage_id']}/Germany",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_get_places_by_country_missing_minor_stage_is_not_handled(client, auth_header, route_graph_data, monkeypatch):
    """
    An unknown minor stage currently raises a ``TypeError`` inside the route.

    Known gap: the route does not check the lookup result for ``None``, so
    Flask would answer with a generic 500 instead of 404. Update this test
    once the route handles the case explicitly.
    """
    monkeypatch.setattr(f"{ROUTES}.get_user_minor_stage", lambda *args, **kwargs: None)

    with pytest.raises(TypeError):
        client.get(
            f"/place-to-visit/get-available-places-by-country/{route_graph_data['minor_stage_id']}/Germany",
            headers=auth_header(route_graph_data["user_id"]),
        )


# ---------------------------------------------------------------------------
# POST /place-to-visit/create-place
# Creating a place for a foreign country is covered in test_security_regressions.py.
# ---------------------------------------------------------------------------


def test_create_place_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid place is stored for the user's custom country."""
    monkeypatch.setattr(VALIDATE_PLACE, stub_validation(True))

    response = client.post(
        "/place-to-visit/create-place",
        json=_place_payload(route_graph_data["custom_country_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(PlaceToVisit).filter_by(name="My Place", user_id=route_graph_data["user_id"])
    ).scalar_one_or_none()
    assert created is not None


def test_create_place_country_not_found(client, auth_header, route_graph_data):
    """Creating a place for an unknown custom country returns 404."""
    response = client.post(
        "/place-to-visit/create-place",
        json=_place_payload(999999),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_create_place_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_PLACE, stub_validation(False))

    response = client.post(
        "/place-to-visit/create-place",
        json=_place_payload(route_graph_data["custom_country_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_place_empty_payload_returns_400(client, auth_header, route_graph_data):
    """A request without any form fields returns 400."""
    response = client.post(
        "/place-to-visit/create-place",
        json={},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /place-to-visit/update-place/<place_id>
# ---------------------------------------------------------------------------


def test_update_place_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid update is applied to the stored place."""
    monkeypatch.setattr(VALIDATE_PLACE, stub_validation(True))

    response = client.post(
        f"/place-to-visit/update-place/{route_graph_data['place_id']}",
        json=_place_payload(route_graph_data["custom_country_id"], name="Updated Place"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(PlaceToVisit, route_graph_data["place_id"]).name == "Updated Place"


def test_update_place_not_found(client, auth_header, route_graph_data):
    """Updating an unknown place returns 404."""
    response = client.post(
        "/place-to-visit/update-place/999999",
        json=_place_payload(route_graph_data["custom_country_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_place_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_PLACE, stub_validation(False))

    response = client.post(
        f"/place-to-visit/update-place/{route_graph_data['place_id']}",
        json=_place_payload(route_graph_data["custom_country_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /place-to-visit/toggle-favorite-place/<place_id>
# POST /place-to-visit/toggle-visited-place/<place_id>
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("toggle", "attribute"),
    [("toggle-favorite-place", "favorite"), ("toggle-visited-place", "visited")],
)
def test_toggle_place_flag_success(client, auth_header, route_graph_data, toggle, attribute):
    """Toggling flips the boolean flag of the place."""
    response = client.post(
        f"/place-to-visit/{toggle}/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert getattr(db.session.get(PlaceToVisit, route_graph_data["place_id"]), attribute) is True


@pytest.mark.parametrize("toggle", ["toggle-favorite-place", "toggle-visited-place"])
def test_toggle_place_flag_not_found(client, auth_header, route_graph_data, toggle):
    """Toggling a flag of an unknown place returns 404."""
    response = client.post(
        f"/place-to-visit/{toggle}/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


@pytest.mark.parametrize("toggle", ["toggle-favorite-place", "toggle-visited-place"])
def test_toggle_place_flag_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch, toggle):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        f"/place-to-visit/{toggle}/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /place-to-visit/delete-place/<place_id>
# ---------------------------------------------------------------------------


def test_delete_place_success(client, auth_header, route_graph_data):
    """Deleting an own place removes it."""
    response = client.delete(
        f"/place-to-visit/delete-place/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(PlaceToVisit, route_graph_data["place_id"]) is None


def test_delete_place_not_found(client, auth_header, route_graph_data):
    """Deleting an unknown place returns 404."""
    response = client.delete(
        "/place-to-visit/delete-place/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_place_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.delete(
        f"/place-to-visit/delete-place/{route_graph_data['place_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /place-to-visit/add-minor-stage-to-place/<place_id>/<minor_stage_id>
# POST /place-to-visit/remove-minor-stage-from-place/<place_id>/<minor_stage_id>
# ---------------------------------------------------------------------------


def test_add_and_remove_minor_stage_link(client, auth_header, route_graph_data):
    """A place can be linked to a minor stage and unlinked again."""
    headers = auth_header(route_graph_data["user_id"])
    ids = (route_graph_data["place_id"], route_graph_data["minor_stage_id"])

    assert client.post(_link_url("add", *ids), headers=headers).status_code == 200
    assert client.post(_link_url("remove", *ids), headers=headers).status_code == 200


@pytest.mark.parametrize("action", ["add", "remove"])
def test_minor_stage_link_resources_not_found(client, auth_header, route_graph_data, action):
    """Linking or unlinking unknown resources returns 404."""
    response = client.post(
        _link_url(action, 999999, 999999),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_add_minor_stage_link_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit while linking is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        _link_url("add", route_graph_data["place_id"], route_graph_data["minor_stage_id"]),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_remove_minor_stage_link_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit while unlinking is reported as 500."""
    headers = auth_header(route_graph_data["user_id"])
    ids = (route_graph_data["place_id"], route_graph_data["minor_stage_id"])
    client.post(_link_url("add", *ids), headers=headers)
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(_link_url("remove", *ids), headers=headers)

    assert response.status_code == 500
