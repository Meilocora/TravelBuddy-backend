"""
Tests for the journey endpoints (``/journey``).

Journey validation and the recalculation of major-stage dates are stubbed
where the test is about route behavior rather than validation rules.
"""

from datetime import datetime, timedelta

import pytest
from helpers import field, raise_error, stub_validation

from app.models import Costs, CustomCountry, Journey, MajorStage, Spendings
from db import db

ROUTES = "app.routes.journey_routes"


def _journey_payload(name="New Journey", countries="Germany"):
    """Builds a complete journey form starting tomorrow."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    return {
        "name": field(name),
        "description": field("desc"),
        "scheduled_start_time": field(tomorrow),
        "scheduled_end_time": field(""),
        "duration_days": field(5),
        "countries": field(countries),
        "budget": field(1000),
        "spent_money": field(0),
    }


def _create_custom_country(name, user_id):
    """Persists a custom country with placeholder details."""
    country = CustomCountry(
        name=name,
        currencies="EUR",
        capital="Capital",
        region="Europe",
        visited=False,
        user_id=user_id,
    )
    db.session.add(country)
    db.session.commit()
    return country


@pytest.fixture()
def valid_update(monkeypatch):
    """Accepts every journey update and skips the major-stage date recalculation."""
    monkeypatch.setattr(f"{ROUTES}.JourneyValidation.validate_journey_update", stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.recalculate_major_stage_dates", lambda journey: None)


def _post_update(client, auth_header, route_graph_data, payload):
    return client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )


# ---------------------------------------------------------------------------
# GET /journey/get-stages-data
# ---------------------------------------------------------------------------


def test_get_stages_data_success(client, auth_header, route_graph_data):
    """All journeys of the user are returned including their stages."""
    response = client.get(
        "/journey/get-stages-data",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "journeys" in response.get_json()


def test_get_stages_data_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """``fetch_journeys`` signals failures by returning an Exception; the route maps it to 500."""
    monkeypatch.setattr(f"{ROUTES}.fetch_journeys", lambda current_user: Exception("Simulated failure"))

    response = client.get(
        "/journey/get-stages-data",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /journey/create-journey
# ---------------------------------------------------------------------------


def test_create_journey_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid journey is stored for the authenticated user."""
    monkeypatch.setattr(f"{ROUTES}.JourneyValidation.validate_journey", stub_validation(True))

    response = client.post(
        "/journey/create-journey",
        json=_journey_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(Journey).filter_by(name="New Journey", user_id=route_graph_data["user_id"])
    ).scalars().first()
    assert created is not None


def test_create_journey_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(f"{ROUTES}.JourneyValidation.validate_journey", stub_validation(False))

    response = client.post(
        "/journey/create-journey",
        json=_journey_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_journey_lookup_error_returns_400(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected error while collecting existing titles returns 400."""
    monkeypatch.setattr(f"{ROUTES}.get_users_stages_titles", raise_error)

    response = client.post(
        "/journey/create-journey",
        json=_journey_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_journey_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.JourneyValidation.validate_journey", stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        "/journey/create-journey",
        json=_journey_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /journey/update-journey/<journey_id>
# ---------------------------------------------------------------------------


def test_update_journey_success(client, auth_header, route_graph_data, valid_update):
    """A valid update is applied to the stored journey."""
    payload = _journey_payload("Routes Journey Updated", countries="Germany, France")

    response = _post_update(client, auth_header, route_graph_data, payload)

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Journey, route_graph_data["journey_id"]).name == "Routes Journey Updated"


def test_update_journey_not_found(client, auth_header, route_graph_data, monkeypatch):
    """Updating a journey the user does not own returns 404."""
    monkeypatch.setattr(f"{ROUTES}.get_user_journey", lambda *args, **kwargs: None)

    response = _post_update(client, auth_header, route_graph_data, _journey_payload())

    assert response.status_code == 404


def test_update_journey_validation_fail_returns_form_values(client, auth_header, route_graph_data, monkeypatch):
    """
    Invalid form values are returned to the client for display.

    Note: the route currently answers with 200 instead of 400 in this case
    (unlike all other update endpoints); this test documents that behavior.
    """
    monkeypatch.setattr(f"{ROUTES}.JourneyValidation.validate_journey_update", stub_validation(False))

    response = _post_update(client, auth_header, route_graph_data, _journey_payload())

    assert response.status_code == 200
    assert "journeyFormValues" in response.get_json()


def test_update_journey_lookup_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected database error while loading related data is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.execute", raise_error)

    response = _post_update(client, auth_header, route_graph_data, _journey_payload())

    assert response.status_code == 500


def test_update_journey_commit_error_returns_500(client, auth_header, route_graph_data, valid_update, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    payload = _journey_payload(countries="Germany, France")
    response = _post_update(client, auth_header, route_graph_data, payload)

    assert response.status_code == 500


def test_update_journey_removes_major_stages_of_removed_country(client, auth_header, route_graph_data, valid_update):
    """Removing a country from a journey deletes the major stages located in it."""
    france_stage = MajorStage(
        title="France Stage",
        scheduled_start_time=datetime(2026, 9, 5, 8, 0),
        scheduled_end_time=datetime(2026, 9, 6, 8, 0),
        duration_days=2,
        additional_info="",
        country="France",
        position=2,
        journey_id=route_graph_data["journey_id"],
    )
    db.session.add(france_stage)
    db.session.flush()
    db.session.add(Costs(major_stage_id=france_stage.id, budget=100, spent_money=0, money_exceeded=False))
    db.session.commit()
    france_stage_id = france_stage.id
    _create_custom_country("France", route_graph_data["user_id"])

    payload = _journey_payload(countries="Germany")
    response = _post_update(client, auth_header, route_graph_data, payload)

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(MajorStage, france_stage_id) is None


def test_update_journey_links_existing_custom_country(client, auth_header, route_graph_data, valid_update):
    """Adding a country the user already has as custom country links it to the journey."""
    _create_custom_country("France", route_graph_data["user_id"])

    payload = _journey_payload(countries="Germany, France")
    response = _post_update(client, auth_header, route_graph_data, payload)

    assert response.status_code == 200


def test_update_journey_response_includes_spendings(client, auth_header, route_graph_data, valid_update):
    """The updated journey in the response contains its spendings."""
    journey_costs = db.session.execute(
        db.select(Costs).filter_by(journey_id=route_graph_data["journey_id"])
    ).scalars().first()
    db.session.add(
        Spendings(
            name="Train",
            amount=20,
            date=datetime(2026, 9, 1, 8, 0),
            category="Transport",
            costs_id=journey_costs.id,
        )
    )
    db.session.commit()

    payload = _journey_payload(countries="Germany, France")
    response = _post_update(client, auth_header, route_graph_data, payload)

    assert response.status_code == 200
    assert "spendings" in response.get_json()["journey"]["costs"]


# ---------------------------------------------------------------------------
# DELETE /journey/delete-journey/<journey_id>
# ---------------------------------------------------------------------------


def test_delete_journey_success(client, auth_header, route_graph_data):
    """Deleting an own journey removes it."""
    response = client.delete(
        f"/journey/delete-journey/{route_graph_data['journey_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Journey, route_graph_data["journey_id"]) is None


def test_delete_journey_not_found(client, auth_header, route_graph_data):
    """Deleting an unknown journey returns 404."""
    response = client.delete(
        "/journey/delete-journey/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_journey_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.delete(
        f"/journey/delete-journey/{route_graph_data['journey_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
