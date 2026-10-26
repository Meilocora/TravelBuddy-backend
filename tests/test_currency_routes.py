"""
Tests for the user-defined currency endpoints (``/currency``).
"""

from helpers import field, raise_error, stub_validation

from app.models import Currency
from db import db

VALIDATE_CURRENCY = "app.routes.currency_routes.CurrencyValidation.validate_currency"


def _currency_payload(code="USD", name="US Dollar", symbol="$", rate=1.1):
    """Builds a complete currency form as sent by the frontend."""
    return {
        "code": field(code),
        "name": field(name),
        "symbol": field(symbol),
        "conversionRate": field(rate),
    }


# ---------------------------------------------------------------------------
# POST /currency/add-currency
# ---------------------------------------------------------------------------


def test_create_currency_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid currency is stored for the authenticated user."""
    monkeypatch.setattr(VALIDATE_CURRENCY, stub_validation(True))

    response = client.post(
        "/currency/add-currency",
        json=_currency_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(Currency).filter_by(code="USD", user_id=route_graph_data["user_id"])
    ).scalars().first()
    assert created is not None


def test_create_currency_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_CURRENCY, stub_validation(False))

    response = client.post(
        "/currency/add-currency",
        json=_currency_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_currency_malformed_json_returns_400(client, auth_header, route_graph_data):
    """A request body that is not valid JSON returns 400."""
    response = client.post(
        "/currency/add-currency",
        data="{bad-json",
        content_type="application/json",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /currency/update-currency/<currency_id>
# ---------------------------------------------------------------------------


def test_update_currency_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid update is applied to the stored currency."""
    monkeypatch.setattr(VALIDATE_CURRENCY, stub_validation(True))

    response = client.post(
        f"/currency/update-currency/{route_graph_data['currency_id']}",
        json=_currency_payload(code="GBP", name="Pound", symbol="£", rate=1.2),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Currency, route_graph_data["currency_id"]).code == "GBP"


def test_update_currency_not_found(client, auth_header, route_graph_data):
    """Updating an unknown currency returns 404."""
    response = client.post(
        "/currency/update-currency/999999",
        json=_currency_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_currency_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_CURRENCY, stub_validation(False))

    response = client.post(
        f"/currency/update-currency/{route_graph_data['currency_id']}",
        json=_currency_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_currency_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_CURRENCY, stub_validation(True))
    monkeypatch.setattr("app.routes.currency_routes.db.session.commit", raise_error)

    response = client.post(
        f"/currency/update-currency/{route_graph_data['currency_id']}",
        json=_currency_payload(code="CAD", name="Canadian Dollar", symbol="C$", rate=1.3),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /currency/delete-currency/<currency_id>
# ---------------------------------------------------------------------------


def test_delete_currency_success(client, auth_header, route_graph_data):
    """Deleting an own currency removes it."""
    response = client.delete(
        f"/currency/delete-currency/{route_graph_data['currency_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Currency, route_graph_data["currency_id"]) is None


def test_delete_currency_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr("app.routes.currency_routes.db.session.commit", raise_error)

    response = client.delete(
        f"/currency/delete-currency/{route_graph_data['currency_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
