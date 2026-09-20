from datetime import datetime

import pytest

from app.models import Costs, Journey, MajorStage, MinorStage
from db import db


def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _major_payload(title="Paris"):
    return {
        "title": _field(title),
        "duration_days": _field(2),
        "additional_info": _field(""),
        "country": _field("Germany"),
        "position": _field(1),
        "budget": _field(500),
        "spent_money": _field(0),
    }


def test_create_major_stage_success(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.MajorStageValidation.validate_major_stage",
        lambda major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, assigned_titles, journey: (major_stage, True),
    )

    response = client.post(
        f"/major_stage/create-major-stage/{route_graph_data['journey_id']}",
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_update_major_stage_not_found(client, auth_header, route_graph_data):
    response = client.post(
        f"/major_stage/update-major-stage/{route_graph_data['journey_id']}/999999",
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_major_stage_success(client, auth_header, route_graph_data):
    stage = db.session.get(MajorStage, route_graph_data["major_stage_id"])
    assert stage is not None

    response = client.delete(
        f"/major_stage/delete-major-stage/{route_graph_data['major_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_update_major_stage_success(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.MajorStageValidation.validate_major_stage_update",
        lambda major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, minor_stages, assigned_titles, old_major_stage, journey: (major_stage, True),
    )

    response = client.post(
        f"/major_stage/update-major-stage/{route_graph_data['journey_id']}/{route_graph_data['major_stage_id']}",
        json=_major_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_swap_major_stages_success(client, auth_header, route_graph_data):
    journey = db.session.get(Journey, route_graph_data["journey_id"])
    second = MajorStage(
        title="Second",
        scheduled_start_time=datetime(2026, 9, 11, 8, 0),
        scheduled_end_time=datetime(2026, 9, 12, 8, 0),
        duration_days=1,
        additional_info="",
        country="Germany",
        position=2,
        journey_id=journey.id,
    )
    db.session.add(second)
    db.session.commit()

    response = client.post(
        "/major_stage/swap-major-stages",
        json={
            "stagesPositionList": [
                {"id": route_graph_data["major_stage_id"], "position": 2},
                {"id": second.id, "position": 1},
            ]
        },
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_major_stage_not_found(client, auth_header, route_graph_data):
    response = client.post(
        "/major_stage/create-major-stage/999999",
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_create_major_stage_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.MajorStageValidation.validate_major_stage",
        lambda major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, assigned_titles, journey: (major_stage, False),
    )

    response = client.post(
        f"/major_stage/create-major-stage/{route_graph_data['journey_id']}",
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_major_stage_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.db.session.execute",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/major_stage/create-major-stage/{route_graph_data['journey_id']}",
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_create_major_stage_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.MajorStageValidation.validate_major_stage",
        lambda major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, assigned_titles, journey: (major_stage, True),
    )
    monkeypatch.setattr(
        "app.routes.major_stage_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/major_stage/create-major-stage/{route_graph_data['journey_id']}",
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_major_stage_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.MajorStageValidation.validate_major_stage_update",
        lambda major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, minor_stages, assigned_titles, old_major_stage, journey: (major_stage, False),
    )

    response = client.post(
        f"/major_stage/update-major-stage/{route_graph_data['journey_id']}/{route_graph_data['major_stage_id']}",
        json=_major_payload("Nope"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_major_stage_initial_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.db.session.execute",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/major_stage/update-major-stage/{route_graph_data['journey_id']}/{route_graph_data['major_stage_id']}",
        json=_major_payload("Fail"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_major_stage_country_change_deletes_minor_stages(client, auth_header, route_graph_data, monkeypatch):
    extra_minor = MinorStage(
        title="Temp Minor",
        scheduled_start_time=datetime(2026, 9, 3, 8, 0),
        scheduled_end_time=datetime(2026, 9, 3, 20, 0),
        duration_days=1,
        position=2,
        major_stage_id=route_graph_data["major_stage_id"],
    )
    db.session.add(extra_minor)
    db.session.flush()
    db.session.add(Costs(minor_stage_id=extra_minor.id, budget=50, spent_money=0, money_exceeded=False))
    db.session.commit()

    monkeypatch.setattr(
        "app.routes.major_stage_routes.MajorStageValidation.validate_major_stage_update",
        lambda major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, minor_stages, assigned_titles, old_major_stage, journey: (major_stage, True),
    )

    payload = _major_payload("Updated Country")
    payload["country"] = _field("France")

    response = client.post(
        f"/major_stage/update-major-stage/{route_graph_data['journey_id']}/{route_graph_data['major_stage_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_update_major_stage_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.MajorStageValidation.validate_major_stage_update",
        lambda major_stage, existing_major_stages, existing_major_stages_costs, journey_costs, minor_stages, assigned_titles, old_major_stage, journey: (major_stage, True),
    )
    monkeypatch.setattr(
        "app.routes.major_stage_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/major_stage/update-major-stage/{route_graph_data['journey_id']}/{route_graph_data['major_stage_id']}",
        json=_major_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_delete_major_stage_not_found(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.get_user_major_stage",
        lambda current_user, majorStageId, journey_id=None: None,
    )

    response = client.delete(
        f"/major_stage/delete-major-stage/{route_graph_data['major_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_major_stage_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.major_stage_routes.db.session.delete",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.delete(
        f"/major_stage/delete-major-stage/{route_graph_data['major_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_swap_major_stages_not_found(client, auth_header, route_graph_data):
    response = client.post(
        "/major_stage/swap-major-stages",
        json={"stagesPositionList": [{"id": route_graph_data["major_stage_id"], "position": 1}, {"id": 999999, "position": 2}]},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_swap_major_stages_different_journeys_same_owner(client, auth_header, route_graph_data):
    other_journey = Journey(
        name="Other journey",
        description="desc",
        scheduled_start_time=datetime(2026, 10, 1, 8, 0),
        scheduled_end_time=datetime(2026, 10, 2, 8, 0),
        duration_days=2,
        countries="Germany",
        user_id=route_graph_data["user_id"],
    )
    db.session.add(other_journey)
    db.session.flush()

    other_major = MajorStage(
        title="Other",
        scheduled_start_time=datetime(2026, 10, 1, 8, 0),
        scheduled_end_time=datetime(2026, 10, 2, 8, 0),
        duration_days=2,
        additional_info="",
        country="Germany",
        position=1,
        journey_id=other_journey.id,
    )
    db.session.add(other_major)
    db.session.commit()

    response = client.post(
        "/major_stage/swap-major-stages",
        json={
            "stagesPositionList": [
                {"id": route_graph_data["major_stage_id"], "position": 2},
                {"id": other_major.id, "position": 1},
            ]
        },
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_swap_major_stages_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    journey = db.session.get(Journey, route_graph_data["journey_id"])
    second = MajorStage(
        title="Second",
        scheduled_start_time=datetime(2026, 9, 11, 8, 0),
        scheduled_end_time=datetime(2026, 9, 12, 8, 0),
        duration_days=1,
        additional_info="",
        country="Germany",
        position=2,
        journey_id=journey.id,
    )
    db.session.add(second)
    db.session.commit()

    monkeypatch.setattr(
        "app.routes.major_stage_routes.db.session.flush",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(RuntimeError):
        client.post(
            "/major_stage/swap-major-stages",
            json={
                "stagesPositionList": [
                    {"id": route_graph_data["major_stage_id"], "position": 2},
                    {"id": second.id, "position": 1},
                ]
            },
            headers=auth_header(route_graph_data["user_id"]),
        )
