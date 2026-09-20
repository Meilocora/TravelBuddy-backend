from datetime import datetime

from app.models import Accommodation, Costs, MajorStage, MinorStage
from db import db


def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _minor_payload(title="Minor New", position=1):
    return {
        "title": _field(title),
        "scheduled_start_time": _field("01.09.2026"),
        "scheduled_end_time": _field("02.09.2026"),
        "duration_days": _field(2),
        "budget": _field(200),
        "spent_money": _field(0),
        "position": _field(position),
        "accommodation_place": _field("Hotel"),
        "accommodation_costs": _field(80),
        "accommodation_booked": _field(False),
        "accommodation_latitude": _field(None),
        "accommodation_longitude": _field(None),
        "accommodation_link": _field(""),
    }



def test_swap_minor_stages_rejects_foreign_stage(
    client,
    auth_header,
    ownership_data,
):
    response = client.post(
        "/minor_stage/swap-minor-stages",
        json={
            "stagesPositionList": [
                {"id": ownership_data["minor_a_id"], "position": 2},
                {"id": ownership_data["minor_b_id"], "position": 3},
            ]
        },
        headers=auth_header(ownership_data["user_a_id"]),
    )

    assert response.status_code == 404


def test_create_minor_stage_success(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.MinorStageValidation.validate_minor_stage",
        lambda minor_stage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, major_stage, old_minor_stage=None: (minor_stage, True),
    )

    response = client.post(
        f"/minor_stage/create-minor-stage/{route_graph_data['major_stage_id']}",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_create_minor_stage_not_found(client, auth_header, route_graph_data):
    response = client.post(
        "/minor_stage/create-minor-stage/999999",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_minor_stage_not_found(client, auth_header, route_graph_data):
    response = client.post(
        f"/minor_stage/update-minor-stage/{route_graph_data['major_stage_id']}/999999",
        json=_minor_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_minor_stage_success(client, auth_header, route_graph_data):
    response = client.delete(
        f"/minor_stage/delete-minor-stage/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_delete_minor_stage_not_found(client, auth_header, route_graph_data):
    response = client.delete(
        "/minor_stage/delete-minor-stage/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_swap_minor_stages_success_same_major(client, auth_header, route_graph_data):
    second = MinorStage(
        title="Second Minor",
        scheduled_start_time=datetime(2026, 9, 2, 8, 0),
        scheduled_end_time=datetime(2026, 9, 3, 8, 0),
        duration_days=1,
        position=2,
        major_stage_id=route_graph_data["major_stage_id"],
    )
    db.session.add(second)
    db.session.flush()
    db.session.add(
        Costs(
            minor_stage_id=second.id,
            budget=100,
            spent_money=0,
            money_exceeded=False,
        )
    )
    db.session.commit()

    response = client.post(
        "/minor_stage/swap-minor-stages",
        json={
            "stagesPositionList": [
                {"id": route_graph_data["minor_stage_id"], "position": 2},
                {"id": second.id, "position": 1},
            ]
        },
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_swap_minor_stages_different_majors(client, auth_header, route_graph_data):
    major = MajorStage(
        title="Second Major",
        scheduled_start_time=datetime(2026, 9, 10, 8, 0),
        scheduled_end_time=datetime(2026, 9, 12, 8, 0),
        duration_days=2,
        additional_info="",
        country="Germany",
        position=3,
        journey_id=route_graph_data["journey_id"],
    )
    db.session.add(major)
    db.session.flush()

    another_minor = MinorStage(
        title="Other Major Minor",
        scheduled_start_time=datetime(2026, 9, 10, 8, 0),
        scheduled_end_time=datetime(2026, 9, 11, 8, 0),
        duration_days=1,
        position=1,
        major_stage_id=major.id,
    )
    db.session.add(another_minor)
    db.session.commit()

    response = client.post(
        "/minor_stage/swap-minor-stages",
        json={
            "stagesPositionList": [
                {"id": route_graph_data["minor_stage_id"], "position": 2},
                {"id": another_minor.id, "position": 1},
            ]
        },
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_minor_stage_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.MinorStageValidation.validate_minor_stage",
        lambda minor_stage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, major_stage, old_minor_stage=None: (minor_stage, False),
    )

    response = client.post(
        f"/minor_stage/create-minor-stage/{route_graph_data['major_stage_id']}",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_minor_stage_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.db.session.execute",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/minor_stage/create-minor-stage/{route_graph_data['major_stage_id']}",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_create_minor_stage_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.MinorStageValidation.validate_minor_stage",
        lambda minor_stage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, major_stage, old_minor_stage=None: (minor_stage, True),
    )
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/minor_stage/create-minor-stage/{route_graph_data['major_stage_id']}",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_minor_stage_without_existing_accommodation_returns_error(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.MinorStageValidation.validate_minor_stage",
        lambda minor_stage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, major_stage, old_minor_stage=None: (minor_stage, True),
    )

    db.session.execute(
        db.delete(Accommodation).where(
            Accommodation.minor_stage_id == route_graph_data["minor_stage_id"]
        )
    )
    db.session.commit()

    response = client.post(
        f"/minor_stage/update-minor-stage/{route_graph_data['major_stage_id']}/{route_graph_data['minor_stage_id']}",
        json=_minor_payload("Updated", 1),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_minor_stage_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.MinorStageValidation.validate_minor_stage",
        lambda minor_stage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, major_stage, old_minor_stage=None: (minor_stage, True),
    )
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/minor_stage/update-minor-stage/{route_graph_data['major_stage_id']}/{route_graph_data['minor_stage_id']}",
        json=_minor_payload("Updated", 1),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_minor_stage_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.MinorStageValidation.validate_minor_stage",
        lambda minor_stage, existing_minor_stages, existing_minor_stages_costs, major_stage_costs, assigned_titles, major_stage, old_minor_stage=None: (minor_stage, False),
    )

    response = client.post(
        f"/minor_stage/update-minor-stage/{route_graph_data['major_stage_id']}/{route_graph_data['minor_stage_id']}",
        json=_minor_payload("Updated", 1),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_minor_stage_initial_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.db.session.execute",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/minor_stage/update-minor-stage/{route_graph_data['major_stage_id']}/{route_graph_data['minor_stage_id']}",
        json=_minor_payload("Updated", 1),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_delete_minor_stage_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.minor_stage_routes.db.session.delete",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.delete(
        f"/minor_stage/delete-minor-stage/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_swap_minor_stages_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    second = MinorStage(
        title="Second Minor",
        scheduled_start_time=datetime(2026, 9, 2, 8, 0),
        scheduled_end_time=datetime(2026, 9, 3, 8, 0),
        duration_days=1,
        position=2,
        major_stage_id=route_graph_data["major_stage_id"],
    )
    db.session.add(second)
    db.session.flush()
    db.session.add(Costs(minor_stage_id=second.id, budget=100, spent_money=0, money_exceeded=False))
    db.session.commit()

    monkeypatch.setattr(
        "app.routes.minor_stage_routes.db.session.flush",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        "/minor_stage/swap-minor-stages",
        json={
            "stagesPositionList": [
                {"id": route_graph_data["minor_stage_id"], "position": 2},
                {"id": second.id, "position": 1},
            ]
        },
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
