"""
Tests for the spending endpoints (``/spending``).

Spendings are booked on the costs of a minor stage. Validation is stubbed
where the test is about route behavior rather than validation rules.
"""

from helpers import field, raise_error, stub_validation

from app.models import Spendings
from db import db

ROUTES = "app.routes.spending_routes"
VALIDATE_SPENDING = f"{ROUTES}.SpendingValidation.validate_spending"


def _spending_payload(name="Taxi"):
    """Builds a complete spending form as sent by the frontend."""
    return {
        "name": field(name),
        "amount": field(12.5),
        "date": field("02.09.2026"),
        "category": field("Transportation"),
    }


def _update_url(minor_stage_id, spending_id):
    return f"/spending/update-spending/{minor_stage_id}/{spending_id}"


# ---------------------------------------------------------------------------
# GET /spending/get-currencies
# ---------------------------------------------------------------------------


def test_get_currencies_success(client, auth_header, route_graph_data):
    """The list of available currencies is returned."""
    response = client.get(
        "/spending/get-currencies",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "currencies" in response.get_json()


# ---------------------------------------------------------------------------
# POST /spending/create-spending/<minor_stage_id>
# ---------------------------------------------------------------------------


def test_create_spending_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid spending is stored."""
    monkeypatch.setattr(VALIDATE_SPENDING, stub_validation(True))

    response = client.post(
        f"/spending/create-spending/{route_graph_data['minor_stage_id']}",
        json=_spending_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(db.select(Spendings).filter_by(name="Taxi")).scalar_one_or_none()
    assert created is not None


def test_create_spending_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_SPENDING, stub_validation(False))

    response = client.post(
        f"/spending/create-spending/{route_graph_data['minor_stage_id']}",
        json=_spending_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_spending_lookup_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected error while loading the minor stage is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.get_user_minor_stage", raise_error)

    response = client.post(
        f"/spending/create-spending/{route_graph_data['minor_stage_id']}",
        json=_spending_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_create_spending_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_SPENDING, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        f"/spending/create-spending/{route_graph_data['minor_stage_id']}",
        json=_spending_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /spending/update-spending/<minor_stage_id>/<spending_id>
# ---------------------------------------------------------------------------


def test_update_spending_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid update is applied to the stored spending."""
    monkeypatch.setattr(VALIDATE_SPENDING, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.calculate_journey_costs", lambda journey_costs: None)

    response = client.post(
        _update_url(route_graph_data["minor_stage_id"], route_graph_data["spending_id"]),
        json=_spending_payload("Updated Taxi"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Spendings, route_graph_data["spending_id"]).name == "Updated Taxi"


def test_update_spending_through_unknown_minor_stage_returns_404(client, auth_header, route_graph_data):
    """A spending can only be updated through the minor stage it belongs to."""
    response = client.post(
        _update_url(999999, route_graph_data["spending_id"]),
        json=_spending_payload("Mismatch"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_spending_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_SPENDING, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        _update_url(route_graph_data["minor_stage_id"], route_graph_data["spending_id"]),
        json=_spending_payload("Err update"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /spending/delete-spending/<spending_id>
# ---------------------------------------------------------------------------


def test_delete_spending_success(client, auth_header, route_graph_data):
    """Deleting an own spending removes it."""
    response = client.delete(
        f"/spending/delete-spending/{route_graph_data['spending_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Spendings, route_graph_data["spending_id"]) is None


def test_delete_spending_not_found(client, auth_header, route_graph_data):
    """Deleting an unknown spending returns 404."""
    response = client.delete(
        "/spending/delete-spending/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_spending_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.delete(
        f"/spending/delete-spending/{route_graph_data['spending_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
