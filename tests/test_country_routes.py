"""
Tests for the country endpoints (``/country``).

``CountryInfo`` (external country database) is replaced by fakes, so the
tests do not depend on the data shipped with the ``countryinfo`` package.
"""

from helpers import raise_error

from app.models import CustomCountry, Journey
from db import db

COUNTRY_INFO = "app.routes.country_routes.CountryInfo"


class FakeCountryInfo:
    """Minimal stand-in for ``countryinfo.CountryInfo`` knowing Germany and France."""

    def __init__(self, name=None):
        self._name = name

    def all(self):
        return {"germany": {}, "france": {}}

    def currencies(self):
        return ["EUR"]

    def languages(self):
        return ["German"]

    def capital(self):
        return "Berlin"

    def population(self):
        return 80

    def region(self):
        return "Europe"

    def subregion(self):
        return "Western Europe"

    def wiki(self):
        return "https://example.com"


class FailingCountryInfo(FakeCountryInfo):
    """``CountryInfo`` fake whose country listing fails."""

    def all(self):
        raise RuntimeError("Simulated failure")


# ---------------------------------------------------------------------------
# GET /country/get-countries/<search>
# ---------------------------------------------------------------------------


def test_get_countries_success(client, auth_header, route_graph_data, monkeypatch):
    """Searching returns a list of matching country names."""
    monkeypatch.setattr(COUNTRY_INFO, FakeCountryInfo)

    response = client.get(
        "/country/get-countries/ger",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "countries" in response.get_json()


def test_get_countries_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing country lookup is reported as 500."""
    monkeypatch.setattr(COUNTRY_INFO, FailingCountryInfo)

    response = client.get(
        "/country/get-countries/ger",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /country/get-custom-countries
# ---------------------------------------------------------------------------


def test_get_custom_countries_success(client, auth_header, route_graph_data):
    """The user's custom countries are returned."""
    response = client.get(
        "/country/get-custom-countries",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "customCountries" in response.get_json()


def test_get_custom_countries_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database query is reported as 500."""

    class _FailingQuery:
        def filter_by(self, **kwargs):
            raise RuntimeError("Simulated failure")

    monkeypatch.setattr("app.routes.country_routes.CustomCountry.query", _FailingQuery())

    response = client.get(
        "/country/get-custom-countries",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /country/create-custom-country
# ---------------------------------------------------------------------------


def test_create_custom_country_success(client, auth_header, route_graph_data, monkeypatch):
    """A known country not yet added by the user is created."""
    monkeypatch.setattr(COUNTRY_INFO, FakeCountryInfo)

    response = client.post(
        "/country/create-custom-country",
        json={"countryName": "France"},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(CustomCountry).filter_by(name="France", user_id=route_graph_data["user_id"])
    ).scalar_one_or_none()
    assert created is not None


def test_create_custom_country_already_exists(client, auth_header, route_graph_data):
    """Adding a country the user already has returns 400."""
    response = client.post(
        "/country/create-custom-country",
        json={"countryName": "Germany"},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_custom_country_unknown_country(client, auth_header, route_graph_data, monkeypatch):
    """A country name unknown to ``CountryInfo`` returns 400."""
    monkeypatch.setattr(COUNTRY_INFO, FakeCountryInfo)

    response = client.post(
        "/country/create-custom-country",
        json={"countryName": "Atlantis"},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_custom_country_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing ``CountryInfo`` lookup is reported as 500."""
    monkeypatch.setattr(COUNTRY_INFO, raise_error)

    response = client.post(
        "/country/create-custom-country",
        json={"countryName": "France"},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /country/update-custom-country/<custom_country_id>
# ---------------------------------------------------------------------------


def test_update_custom_country_success(client, auth_header, route_graph_data):
    """The editable country details are updated."""
    payload = {
        "currencies": {"value": ["EUR", "USD"]},
        "languages": {"value": ["German", "English"]},
        "capital": {"value": "Berlin"},
        "population": {"value": 100},
        "region": {"value": "Europe"},
        "subregion": {"value": "Western Europe"},
        "visum_regulations": {"value": "None"},
        "best_time_to_visit": {"value": "Summer"},
        "general_information": {"value": "Nice"},
    }

    response = client.post(
        f"/country/update-custom-country/{route_graph_data['custom_country_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    country = db.session.get(CustomCountry, route_graph_data["custom_country_id"])
    assert country.best_time_to_visit == "Summer"


def test_update_custom_country_not_found(client, auth_header, route_graph_data):
    """Updating an unknown custom country returns 404."""
    response = client.post(
        "/country/update-custom-country/999999",
        json={},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_custom_country_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr("app.routes.country_routes.db.session.commit", raise_error)

    response = client.post(
        f"/country/update-custom-country/{route_graph_data['custom_country_id']}",
        json={"currencies": {"value": ["EUR"]}},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /country/delete-custom-country/<custom_country_id>
# ---------------------------------------------------------------------------


def _create_unlinked_country(user_id):
    """Creates a custom country that is not referenced by any journey."""
    country = CustomCountry(name="Unlinked", visited=False, user_id=user_id)
    db.session.add(country)
    db.session.commit()
    return country


def test_delete_custom_country_success(client, auth_header, route_graph_data):
    """A country not used by any journey can be deleted."""
    country = _create_unlinked_country(route_graph_data["user_id"])
    country_id = country.id

    response = client.delete(
        f"/country/delete-custom-country/{country_id}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(CustomCountry, country_id) is None


def test_delete_custom_country_linked_to_journey_returns_400(client, auth_header, route_graph_data):
    """A country still used by a journey must not be deleted."""
    journey = db.session.get(Journey, route_graph_data["journey_id"])
    journey.countries = "Germany"
    db.session.commit()

    response = client.delete(
        f"/country/delete-custom-country/{route_graph_data['custom_country_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_delete_custom_country_not_found(client, auth_header, route_graph_data):
    """Deleting an unknown custom country returns 404."""
    response = client.delete(
        "/country/delete-custom-country/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_custom_country_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    country = _create_unlinked_country(route_graph_data["user_id"])
    monkeypatch.setattr("app.routes.country_routes.db.session.commit", raise_error)

    response = client.delete(
        f"/country/delete-custom-country/{country.id}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
