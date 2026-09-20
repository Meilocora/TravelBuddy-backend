from app.models import Currency
from db import db


def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _currency_payload(code="USD", name="US Dollar", symbol="$", rate=1.1):
    return {
        "code": _field(code),
        "name": _field(name),
        "symbol": _field(symbol),
        "conversionRate": _field(rate),
    }


def test_create_currency_success(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.currency_routes.CurrencyValidation.validate_currency",
        lambda currency: (currency, True),
    )

    response = client.post(
        "/currency/add-currency",
        json=_currency_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    created = db.session.execute(
        db.select(Currency).filter_by(code="USD", user_id=route_graph_data["user_id"])
    ).scalars().first()
    assert created is not None


def test_update_currency_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.post(
        "/currency/update-currency/999999",
        json=_currency_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_currency_success(
    client,
    auth_header,
    route_graph_data,
):
    response = client.delete(
        f"/currency/delete-currency/{route_graph_data['currency_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_update_currency_success(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.currency_routes.CurrencyValidation.validate_currency",
        lambda currency: (currency, True),
    )

    response = client.post(
        f"/currency/update-currency/{route_graph_data['currency_id']}",
        json=_currency_payload(code="GBP", name="Pound", symbol="£", rate=1.2),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_currency_validation_fail(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    payload = _currency_payload()
    payload["name"]["errors"] = ["x"]

    monkeypatch.setattr(
        "app.routes.currency_routes.CurrencyValidation.validate_currency",
        lambda currency: (payload, False),
    )

    response = client.post(
        "/currency/add-currency",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_currency_bad_json_returns_400(
    client,
    auth_header,
    route_graph_data,
):
    response = client.post(
        "/currency/add-currency",
        data="{bad-json",
        content_type="application/json",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_currency_validation_fail(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    payload = _currency_payload()
    monkeypatch.setattr(
        "app.routes.currency_routes.CurrencyValidation.validate_currency",
        lambda currency: (payload, False),
    )

    response = client.post(
        f"/currency/update-currency/{route_graph_data['currency_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_update_currency_commit_exception_returns_500(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.currency_routes.CurrencyValidation.validate_currency",
        lambda currency: (currency, True),
    )

    def _raise():
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routes.currency_routes.db.session.commit",
        _raise,
    )

    response = client.post(
        f"/currency/update-currency/{route_graph_data['currency_id']}",
        json=_currency_payload(code="CAD", name="Canadian Dollar", symbol="C$", rate=1.3),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_delete_currency_commit_exception_returns_500(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    def _raise():
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routes.currency_routes.db.session.commit",
        _raise,
    )

    response = client.delete(
        f"/currency/delete-currency/{route_graph_data['currency_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
