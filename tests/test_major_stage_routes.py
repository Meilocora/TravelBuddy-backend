"""
Tests for the major stage endpoints (``/major_stage``).

Major stages belong to a journey and are ordered by ``position``.
Validation is stubbed where the test is about route behavior.
"""

from datetime import datetime

import pytest
from helpers import field, raise_error, stub_validation

from app.models import Costs, Journey, MajorStage, MinorStage
from db import db

ROUTES = "app.routes.major_stage_routes"
VALIDATE_CREATE = f"{ROUTES}.MajorStageValidation.validate_major_stage"
VALIDATE_UPDATE = f"{ROUTES}.MajorStageValidation.validate_major_stage_update"


def _major_payload(title="Paris", country="Germany"):
    """Builds a complete major stage form as sent by the frontend."""
    return {
        "title": field(title),
        "duration_days": field(2),
        "additional_info": field(""),
        "country": field(country),
        "position": field(1),
        "budget": field(500),
        "spent_money": field(0),
    }


def _create_major_stage(journey_id, title="Second", position=2, start=datetime(2026, 9, 11, 8, 0)):
    """Persists an additional major stage in the given journey."""
    stage = MajorStage(
        title=title,
        scheduled_start_time=start,
        scheduled_end_time=start.replace(day=start.day + 1),
        duration_days=1,
        additional_info="",
        country="Germany",
        position=position,
        journey_id=journey_id,
    )
    db.session.add(stage)
    db.session.commit()
    return stage


def _create_url(journey_id):
    return f"/major_stage/create-major-stage/{journey_id}"


def _update_url(journey_id, major_stage_id):
    return f"/major_stage/update-major-stage/{journey_id}/{major_stage_id}"


def _swap_payload(*id_position_pairs):
    return {
        "stagesPositionList": [
            {"id": stage_id, "position": position} for stage_id, position in id_position_pairs
        ]
    }


# ---------------------------------------------------------------------------
# POST /major_stage/create-major-stage/<journey_id>
# ---------------------------------------------------------------------------


def test_create_major_stage_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid major stage is stored in the journey."""
    monkeypatch.setattr(VALIDATE_CREATE, stub_validation(True))

    response = client.post(
        _create_url(route_graph_data["journey_id"]),
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(MajorStage).filter_by(title="Paris", journey_id=route_graph_data["journey_id"])
    ).scalar_one_or_none()
    assert created is not None


def test_create_major_stage_journey_not_found(client, auth_header, route_graph_data):
    """Creating a major stage in an unknown journey returns 404."""
    response = client.post(
        _create_url(999999),
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_create_major_stage_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_CREATE, stub_validation(False))

    response = client.post(
        _create_url(route_graph_data["journey_id"]),
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_major_stage_lookup_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected database error while loading related data is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.execute", raise_error)

    response = client.post(
        _create_url(route_graph_data["journey_id"]),
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_create_major_stage_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_CREATE, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        _create_url(route_graph_data["journey_id"]),
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /major_stage/update-major-stage/<journey_id>/<major_stage_id>
# ---------------------------------------------------------------------------


def test_update_major_stage_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid update is applied to the stored major stage."""
    monkeypatch.setattr(VALIDATE_UPDATE, stub_validation(True))

    response = client.post(
        _update_url(route_graph_data["journey_id"], route_graph_data["major_stage_id"]),
        json=_major_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(MajorStage, route_graph_data["major_stage_id"]).title == "Updated"


def test_update_major_stage_not_found(client, auth_header, route_graph_data):
    """Updating an unknown major stage returns 404."""
    response = client.post(
        _update_url(route_graph_data["journey_id"], 999999),
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_major_stage_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_UPDATE, stub_validation(False))

    response = client.post(
        _update_url(route_graph_data["journey_id"], route_graph_data["major_stage_id"]),
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_major_stage_lookup_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected database error while loading related data is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.execute", raise_error)

    response = client.post(
        _update_url(route_graph_data["journey_id"], route_graph_data["major_stage_id"]),
        json=_major_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_major_stage_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_UPDATE, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        _update_url(route_graph_data["journey_id"], route_graph_data["major_stage_id"]),
        json=_major_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_major_stage_country_change_deletes_minor_stages(client, auth_header, route_graph_data, monkeypatch):
    """Changing the country of a major stage removes its minor stages."""
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
    extra_minor_id = extra_minor.id

    monkeypatch.setattr(VALIDATE_UPDATE, stub_validation(True))

    response = client.post(
        _update_url(route_graph_data["journey_id"], route_graph_data["major_stage_id"]),
        json=_major_payload("Updated Country", country="France"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(MinorStage, extra_minor_id) is None


# ---------------------------------------------------------------------------
# DELETE /major_stage/delete-major-stage/<major_stage_id>
# ---------------------------------------------------------------------------


def test_delete_major_stage_success(client, auth_header, route_graph_data):
    """Deleting an own major stage removes it."""
    response = client.delete(
        f"/major_stage/delete-major-stage/{route_graph_data['major_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(MajorStage, route_graph_data["major_stage_id"]) is None


def test_delete_foreign_major_stage_returns_404(client, auth_header, ownership_data):
    """Deleting another user's major stage returns 404 and keeps the stage."""
    response = client.delete(
        f"/major_stage/delete-major-stage/{ownership_data['major_b_id']}",
        headers=auth_header(ownership_data["user_a_id"]),
    )

    assert response.status_code == 404
    assert db.session.get(MajorStage, ownership_data["major_b_id"]) is not None


@pytest.mark.xfail(
    raises=AttributeError,
    strict=True,
    reason="Known bug: the route dereferences the journey before checking that the stage exists.",
)
def test_delete_unknown_major_stage_returns_404(client, auth_header, route_graph_data):
    """Deleting a non-existent major stage should return 404."""
    response = client.delete(
        "/major_stage/delete-major-stage/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_major_stage_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database delete is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.delete", raise_error)

    response = client.delete(
        f"/major_stage/delete-major-stage/{route_graph_data['major_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /major_stage/swap-major-stages
# ---------------------------------------------------------------------------


def test_swap_major_stages_success(client, auth_header, route_graph_data):
    """Two major stages of the same journey swap their positions."""
    first_id = route_graph_data["major_stage_id"]
    second_id = _create_major_stage(route_graph_data["journey_id"]).id

    response = client.post(
        "/major_stage/swap-major-stages",
        json=_swap_payload((first_id, 2), (second_id, 1)),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(MajorStage, first_id).position == 2
    assert db.session.get(MajorStage, second_id).position == 1


def test_swap_major_stages_not_found(client, auth_header, route_graph_data):
    """A swap containing an unknown stage returns 404."""
    response = client.post(
        "/major_stage/swap-major-stages",
        json=_swap_payload((route_graph_data["major_stage_id"], 1), (999999, 2)),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_swap_major_stages_of_different_journeys_returns_400(client, auth_header, route_graph_data):
    """Stages of different journeys cannot be swapped, even for the same owner."""
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
    db.session.commit()
    other_stage = _create_major_stage(
        other_journey.id, title="Other", position=1, start=datetime(2026, 10, 1, 8, 0)
    )

    response = client.post(
        "/major_stage/swap-major-stages",
        json=_swap_payload((route_graph_data["major_stage_id"], 2), (other_stage.id, 1)),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_swap_major_stages_flush_error_is_not_handled(client, auth_header, route_graph_data, monkeypatch):
    """
    A database error during the swap currently propagates out of the route.

    Known gap: unlike ``swap-minor-stages`` the route has no error handling,
    so Flask would answer with a generic 500. Update this test once the route
    catches the error itself.
    """
    second_id = _create_major_stage(route_graph_data["journey_id"]).id
    monkeypatch.setattr(f"{ROUTES}.db.session.flush", raise_error)

    with pytest.raises(RuntimeError):
        client.post(
            "/major_stage/swap-major-stages",
            json=_swap_payload((route_graph_data["major_stage_id"], 2), (second_id, 1)),
            headers=auth_header(route_graph_data["user_id"]),
        )
