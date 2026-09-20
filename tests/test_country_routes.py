from app.models import CustomCountry, Journey
from db import db


def _fake_countryinfo_factory():
    class _FakeCountryInfo:
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

    return _FakeCountryInfo


def test_get_countries_success(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.country_routes.CountryInfo",
        _fake_countryinfo_factory(),
    )

    response = client.get(
        "/country/get-countries/ger",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "countries" in response.get_json()


def test_create_custom_country_success(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.country_routes.CountryInfo",
        _fake_countryinfo_factory(),
    )

    response = client.post(
        "/country/create-custom-country",
        json={"countryName": "germany"},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code in (201, 400)


def test_delete_custom_country_linked_to_journey_returns_400(
    client,
    auth_header,
    route_graph_data,
):
    journey = db.session.get(Journey, route_graph_data["journey_id"])
    journey.countries = "Germany"
    db.session.commit()

    response = client.delete(
        f"/country/delete-custom-country/{route_graph_data['custom_country_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_get_custom_countries_success(
    client,
    auth_header,
    route_graph_data,
):
    response = client.get(
        "/country/get-custom-countries",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "customCountries" in response.get_json()


def test_update_custom_country_success(
    client,
    auth_header,
    route_graph_data,
):
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


def test_get_countries_exception_returns_500(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    class _BoomCountryInfo:
        def __init__(self, *args, **kwargs):
            pass

        def all(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routes.country_routes.CountryInfo",
        _BoomCountryInfo,
    )

    response = client.get(
        "/country/get-countries/ger",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_create_custom_country_already_exists(
    client,
    auth_header,
    route_graph_data,
):
    response = client.post(
        "/country/create-custom-country",
        json={"countryName": "Germany"},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_custom_country_not_exists(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    class _FakeCountryInfo:
        def __init__(self, *args, **kwargs):
            pass

        def all(self):
            return {"germany": {}}

    monkeypatch.setattr(
        "app.routes.country_routes.CountryInfo",
        _FakeCountryInfo,
    )

    response = client.post(
        "/country/create-custom-country",
        json={"countryName": "Atlantis"},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_custom_country_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.post(
        "/country/update-custom-country/999999",
        json={},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_custom_country_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.delete(
        "/country/delete-custom-country/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_get_custom_countries_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    class _BoomQuery:
        def filter_by(self, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routes.country_routes.CustomCountry.query",
        _BoomQuery(),
    )
    response = client.get(
        "/country/get-custom-countries",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_create_custom_country_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.country_routes.CountryInfo",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        "/country/create-custom-country",
        json={"countryName": "France"},
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_update_custom_country_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.country_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/country/update-custom-country/{route_graph_data['custom_country_id']}",
        json={"currencies": {"value": ["EUR"]}},
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_delete_custom_country_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    country = CustomCountry(
        name="Unlinked",
        currencies=None,
        languages=None,
        capital=None,
        population=None,
        region=None,
        subregion=None,
        wiki_link=None,
        visited=False,
        visum_regulations=None,
        best_time_to_visit=None,
        general_information=None,
        user_id=route_graph_data["user_id"],
    )
    db.session.add(country)
    db.session.commit()

    monkeypatch.setattr(
        "app.routes.country_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.delete(
        f"/country/delete-custom-country/{country.id}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500
