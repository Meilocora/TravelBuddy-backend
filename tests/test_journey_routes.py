from datetime import datetime, timedelta

from app.models import Costs, CustomCountry, Journey, MajorStage, Spendings
from db import db


def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _journey_payload(name="New Journey"):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    return {
        "name": _field(name),
        "description": _field("desc"),
        "scheduled_start_time": _field(tomorrow),
        "scheduled_end_time": _field(""),
        "duration_days": _field(5),
        "countries": _field("Germany"),
        "budget": _field(1000),
        "spent_money": _field(0),
    }


def test_get_stages_data_success(client, auth_header, route_graph_data):
    response = client.get(
        "/journey/get-stages-data",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "journeys" in response.get_json()


def test_create_journey_success(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey",
        lambda journey, existing_journeys, assigned_titles: (journey, True),
    )

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


def test_update_journey_success(client, auth_header, route_graph_data, monkeypatch):
    payload = _journey_payload("Routes Journey Updated")
    payload["spent_money"] = _field(0)
    payload["countries"] = _field("Germany, France")

    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey_update",
        lambda journey, existing_journeys, major_stages, assigned_titles, old_journey: (journey, True),
    )
    monkeypatch.setattr(
        "app.routes.journey_routes.recalculate_major_stage_dates",
        lambda journey: None,
    )

    response = client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_delete_journey_success(client, auth_header, route_graph_data):
    response = client.delete(
        f"/journey/delete-journey/{route_graph_data['journey_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_delete_journey_not_found(client, auth_header, route_graph_data):
    response = client.delete(
        "/journey/delete-journey/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 404


def test_get_stages_data_error_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.journey_routes.fetch_journeys",
        lambda current_user: Exception("boom"),
    )

    response = client.get(
        "/journey/get-stages-data",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_create_journey_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = _journey_payload("Fail Journey")
    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey",
        lambda journey, existing_journeys, assigned_titles: (journey, False),
    )

    response = client.post(
        "/journey/create-journey",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 200


def test_update_journey_not_found(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.journey_routes.get_user_journey",
        lambda current_user, journeyId: None,
    )

    response = client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=_journey_payload("No Journey"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 404


def test_update_journey_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = _journey_payload("Validation Fail")
    payload["spent_money"] = _field(0)
    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey_update",
        lambda journey, existing_journeys, major_stages, assigned_titles, old_journey: (journey, False),
    )

    response = client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 200


def test_create_journey_unknown_error_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.journey_routes.get_users_stages_titles",
        lambda current_user: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        "/journey/create-journey",
        json=_journey_payload("X"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_create_journey_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey",
        lambda journey, existing_journeys, assigned_titles: (journey, True),
    )
    monkeypatch.setattr(
        "app.routes.journey_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        "/journey/create-journey",
        json=_journey_payload("Err Commit"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_update_journey_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    payload = _journey_payload("Err Update")
    payload["spent_money"] = _field(0)
    payload["countries"] = _field("Germany, France")

    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey_update",
        lambda journey, existing_journeys, major_stages, assigned_titles, old_journey: (journey, True),
    )
    monkeypatch.setattr(
        "app.routes.journey_routes.recalculate_major_stage_dates",
        lambda journey: None,
    )
    monkeypatch.setattr(
        "app.routes.journey_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_delete_journey_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.journey_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.delete(
        f"/journey/delete-journey/{route_graph_data['journey_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_update_journey_initial_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.journey_routes.db.session.execute",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=_journey_payload("Init Boom"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_journey_removes_missing_country_major_stages(client, auth_header, route_graph_data, monkeypatch):
    major_stage = MajorStage(
        title="France Stage",
        scheduled_start_time=datetime(2026, 9, 5, 8, 0),
        scheduled_end_time=datetime(2026, 9, 6, 8, 0),
        duration_days=2,
        additional_info="",
        country="France",
        position=2,
        journey_id=route_graph_data["journey_id"],
    )
    db.session.add(major_stage)
    db.session.flush()
    db.session.add(Costs(major_stage_id=major_stage.id, budget=100, spent_money=0, money_exceeded=False))
    db.session.commit()

    db.session.add(
        CustomCountry(
            name="France",
            currencies="EUR",
            languages="French",
            capital="Paris",
            population=100,
            region="Europe",
            subregion="Western Europe",
            wiki_link="https://example.com",
            visited=False,
            visum_regulations=None,
            best_time_to_visit=None,
            general_information=None,
            user_id=route_graph_data["user_id"],
        )
    )
    db.session.commit()

    payload = _journey_payload("Country Delete")
    payload["countries"] = _field("Germany")

    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey_update",
        lambda journey, existing_journeys, major_stages, assigned_titles, old_journey: (journey, True),
    )
    monkeypatch.setattr(
        "app.routes.journey_routes.recalculate_major_stage_dates",
        lambda journey: None,
    )

    response = client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_update_journey_adds_existing_custom_country_link(client, auth_header, route_graph_data, monkeypatch):
    france_custom = CustomCountry(
        name="France",
        currencies="EUR",
        languages="French",
        capital="Paris",
        population=100,
        region="Europe",
        subregion="Western Europe",
        wiki_link="https://example.com",
        visited=False,
        visum_regulations=None,
        best_time_to_visit=None,
        general_information=None,
        user_id=route_graph_data["user_id"],
    )
    db.session.add(france_custom)
    db.session.commit()

    payload = _journey_payload("Country Add")
    payload["countries"] = _field("Germany, France")

    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey_update",
        lambda journey, existing_journeys, major_stages, assigned_titles, old_journey: (journey, True),
    )
    monkeypatch.setattr(
        "app.routes.journey_routes.recalculate_major_stage_dates",
        lambda journey: None,
    )

    response = client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_update_journey_response_with_spendings(client, auth_header, route_graph_data, monkeypatch):
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

    payload = _journey_payload("Spending Journey")
    payload["countries"] = _field("Germany, France")

    monkeypatch.setattr(
        "app.routes.journey_routes.JourneyValidation.validate_journey_update",
        lambda journey, existing_journeys, major_stages, assigned_titles, old_journey: (journey, True),
    )
    monkeypatch.setattr(
        "app.routes.journey_routes.recalculate_major_stage_dates",
        lambda journey: None,
    )

    response = client.post(
        f"/journey/update-journey/{route_graph_data['journey_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "spendings" in response.get_json()["journey"]["costs"]
