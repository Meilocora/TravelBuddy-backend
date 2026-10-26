"""
Tests for the minor stage endpoints (``/minor_stage``).

Minor stages belong to a major stage, are ordered by ``position`` and carry
an accommodation. Validation is stubbed where the test is about route
behavior rather than validation rules.
"""

from datetime import datetime, timedelta

from helpers import field, raise_error, stub_validation

from app.models import Accommodation, Costs, Journey, MajorStage, MinorStage, User
from db import db

ROUTES = "app.routes.minor_stage_routes"
VALIDATE_MINOR_STAGE = f"{ROUTES}.MinorStageValidation.validate_minor_stage"


def _minor_payload(title="Minor New", position=1, start="01.09.2026", end="02.09.2026", **overrides):
    """Builds a complete minor stage form; ``overrides`` replace single field values."""
    values = {
        "title": title,
        "scheduled_start_time": start,
        "scheduled_end_time": end,
        "duration_days": 2,
        "budget": 200,
        "spent_money": 0,
        "position": position,
        "accommodation_place": "Hotel",
        "accommodation_costs": 80,
        "accommodation_booked": False,
        "accommodation_latitude": None,
        "accommodation_longitude": None,
        "accommodation_link": "",
    }
    values.update(overrides)
    return {key: field(value) for key, value in values.items()}


def _create_minor_stage(major_stage_id, title="Second Minor", position=2, start=datetime(2026, 9, 2, 8, 0)):
    """Persists an additional minor stage (with costs) in the given major stage."""
    stage = MinorStage(
        title=title,
        scheduled_start_time=start,
        scheduled_end_time=start + timedelta(days=1),
        duration_days=1,
        position=position,
        major_stage_id=major_stage_id,
    )
    db.session.add(stage)
    db.session.flush()
    db.session.add(Costs(minor_stage_id=stage.id, budget=100, spent_money=0, money_exceeded=False))
    db.session.commit()
    return stage


def _create_stage_with_accommodation():
    """
    Creates a dedicated user with a journey -> major stage -> minor stage chain,
    costs on every level and an accommodation ("Old Hotel") for the minor stage.

    Unlike ``route_graph_data`` this graph includes an accommodation, which the
    update endpoint requires.
    """
    start = datetime(2026, 9, 1)
    end = datetime(2026, 9, 10)
    user = User(username="minor-stage-user", email="minor-stage@example.com", password="password")
    journey = Journey(
        name="Minor stage update journey",
        description="",
        scheduled_start_time=start,
        scheduled_end_time=end,
        duration_days=(end - start).days,
        countries="Germany",
        user=user,
    )
    major_stage = MajorStage(
        title="Germany",
        scheduled_start_time=start,
        scheduled_end_time=end,
        duration_days=(end - start).days,
        additional_info=None,
        country="Germany",
        position=1,
        journey=journey,
    )
    minor_stage = MinorStage(
        title="Old stop",
        scheduled_start_time=start,
        scheduled_end_time=end,
        duration_days=(end - start).days,
        position=1,
        major_stage=major_stage,
    )
    db.session.add_all([user, journey, major_stage, minor_stage])
    db.session.flush()
    db.session.add_all([
        Costs(journey_id=journey.id, budget=2000, spent_money=0, money_exceeded=False),
        Costs(major_stage_id=major_stage.id, budget=1000, spent_money=0, money_exceeded=False),
        Costs(minor_stage_id=minor_stage.id, budget=300, spent_money=0, money_exceeded=False),
        Accommodation(
            minor_stage_id=minor_stage.id,
            place="Old Hotel",
            costs=80,
            booked=False,
            latitude=1.0,
            longitude=2.0,
            link="",
        ),
    ])
    db.session.commit()
    return user.id, major_stage.id, minor_stage.id


def _accommodation_update_payload():
    """Valid update payload for ``_create_stage_with_accommodation`` (starts tomorrow)."""
    tomorrow = datetime.now() + timedelta(days=1)
    return _minor_payload(
        title="Updated stop",
        start=tomorrow.strftime("%d.%m.%Y"),
        end=(tomorrow + timedelta(days=1)).strftime("%d.%m.%Y"),
        duration_days=1,
        budget=400,
        accommodation_place="New Hotel",
        accommodation_costs=120,
        accommodation_booked=True,
        accommodation_latitude=48.137154,
        accommodation_longitude=11.576124,
    )


def _update_url(major_stage_id, minor_stage_id):
    return f"/minor_stage/update-minor-stage/{major_stage_id}/{minor_stage_id}"


def _swap_payload(*id_position_pairs):
    return {
        "stagesPositionList": [
            {"id": stage_id, "position": position} for stage_id, position in id_position_pairs
        ]
    }


# ---------------------------------------------------------------------------
# POST /minor_stage/create-minor-stage/<major_stage_id>
# ---------------------------------------------------------------------------


def test_create_minor_stage_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid minor stage is stored in the major stage."""
    monkeypatch.setattr(VALIDATE_MINOR_STAGE, stub_validation(True))

    response = client.post(
        f"/minor_stage/create-minor-stage/{route_graph_data['major_stage_id']}",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(MinorStage).filter_by(title="Minor New", major_stage_id=route_graph_data["major_stage_id"])
    ).scalar_one_or_none()
    assert created is not None


def test_create_minor_stage_major_stage_not_found(client, auth_header, route_graph_data):
    """Creating a minor stage in an unknown major stage returns 404."""
    response = client.post(
        "/minor_stage/create-minor-stage/999999",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_create_minor_stage_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_MINOR_STAGE, stub_validation(False))

    response = client.post(
        f"/minor_stage/create-minor-stage/{route_graph_data['major_stage_id']}",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_create_minor_stage_lookup_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected database error while loading related data is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.execute", raise_error)

    response = client.post(
        f"/minor_stage/create-minor-stage/{route_graph_data['major_stage_id']}",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_create_minor_stage_commit_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_MINOR_STAGE, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        f"/minor_stage/create-minor-stage/{route_graph_data['major_stage_id']}",
        json=_minor_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /minor_stage/update-minor-stage/<major_stage_id>/<minor_stage_id>
# ---------------------------------------------------------------------------


def test_update_minor_stage_updates_accommodation_and_coordinates(client, auth_header):
    """The update is applied to the minor stage and its accommodation, incl. coordinates."""
    user_id, major_stage_id, minor_stage_id = _create_stage_with_accommodation()

    response = client.post(
        _update_url(major_stage_id, minor_stage_id),
        json=_accommodation_update_payload(),
        headers=auth_header(user_id),
    )

    assert response.status_code == 200
    accommodation_json = response.get_json()["minorStage"]["accommodation"]
    assert accommodation_json["place"] == "New Hotel"
    assert accommodation_json["latitude"] == 48.137154
    assert accommodation_json["longitude"] == 11.576124

    accommodation = db.session.execute(
        db.select(Accommodation).filter_by(minor_stage_id=minor_stage_id)
    ).scalar_one()
    assert accommodation.place == "New Hotel"
    assert accommodation.latitude == 48.137154
    assert accommodation.longitude == 11.576124


def test_update_minor_stage_rolls_back_when_cost_recalculation_fails(client, auth_header, monkeypatch):
    """If the cost recalculation fails, no partial changes are persisted."""
    user_id, major_stage_id, minor_stage_id = _create_stage_with_accommodation()
    monkeypatch.setattr(f"{ROUTES}.calculate_journey_costs", raise_error)

    response = client.post(
        _update_url(major_stage_id, minor_stage_id),
        json=_accommodation_update_payload(),
        headers=auth_header(user_id),
    )

    assert response.status_code == 500
    db.session.expire_all()
    minor_stage = db.session.get(MinorStage, minor_stage_id)
    accommodation = db.session.execute(
        db.select(Accommodation).filter_by(minor_stage_id=minor_stage_id)
    ).scalar_one()
    assert minor_stage.title == "Old stop"
    assert accommodation.place == "Old Hotel"
    assert accommodation.latitude == 1.0
    assert accommodation.longitude == 2.0


def test_update_minor_stage_not_found(client, auth_header, route_graph_data):
    """Updating an unknown minor stage returns 404."""
    response = client.post(
        _update_url(route_graph_data["major_stage_id"], 999999),
        json=_minor_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_minor_stage_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_MINOR_STAGE, stub_validation(False))

    response = client.post(
        _update_url(route_graph_data["major_stage_id"], route_graph_data["minor_stage_id"]),
        json=_minor_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_minor_stage_without_accommodation_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """
    Updating a minor stage that has no accommodation fails with 500.

    The fixture's minor stage is created without an accommodation; the route
    expects one to exist and does not create it on demand.
    """
    monkeypatch.setattr(VALIDATE_MINOR_STAGE, stub_validation(True))

    response = client.post(
        _update_url(route_graph_data["major_stage_id"], route_graph_data["minor_stage_id"]),
        json=_minor_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_minor_stage_lookup_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected database error while loading related data is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.execute", raise_error)

    response = client.post(
        _update_url(route_graph_data["major_stage_id"], route_graph_data["minor_stage_id"]),
        json=_minor_payload("Updated"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_update_minor_stage_commit_error_returns_500(client, auth_header, monkeypatch):
    """A failing database commit is reported as 500."""
    user_id, major_stage_id, minor_stage_id = _create_stage_with_accommodation()
    monkeypatch.setattr(VALIDATE_MINOR_STAGE, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(
        _update_url(major_stage_id, minor_stage_id),
        json=_accommodation_update_payload(),
        headers=auth_header(user_id),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /minor_stage/delete-minor-stage/<minor_stage_id>
# ---------------------------------------------------------------------------


def test_delete_minor_stage_success(client, auth_header, route_graph_data):
    """Deleting an own minor stage removes it."""
    response = client.delete(
        f"/minor_stage/delete-minor-stage/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(MinorStage, route_graph_data["minor_stage_id"]) is None


def test_delete_minor_stage_not_found(client, auth_header, route_graph_data):
    """Deleting an unknown minor stage returns 404."""
    response = client.delete(
        "/minor_stage/delete-minor-stage/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_minor_stage_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A failing database delete is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.delete", raise_error)

    response = client.delete(
        f"/minor_stage/delete-minor-stage/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /minor_stage/swap-minor-stages
# Swapping a foreign stage is covered in test_security_regressions.py.
# ---------------------------------------------------------------------------


def test_swap_minor_stages_success(client, auth_header, route_graph_data):
    """Two minor stages of the same major stage swap their positions."""
    first_id = route_graph_data["minor_stage_id"]
    second_id = _create_minor_stage(route_graph_data["major_stage_id"]).id

    response = client.post(
        "/minor_stage/swap-minor-stages",
        json=_swap_payload((first_id, 2), (second_id, 1)),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(MinorStage, first_id).position == 2
    assert db.session.get(MinorStage, second_id).position == 1


def test_swap_minor_stages_of_different_major_stages_returns_400(client, auth_header, route_graph_data):
    """Stages of different major stages cannot be swapped, even for the same owner."""
    other_major = MajorStage(
        title="Second Major",
        scheduled_start_time=datetime(2026, 9, 10, 8, 0),
        scheduled_end_time=datetime(2026, 9, 12, 8, 0),
        duration_days=2,
        additional_info="",
        country="Germany",
        position=3,
        journey_id=route_graph_data["journey_id"],
    )
    db.session.add(other_major)
    db.session.commit()
    other_minor = _create_minor_stage(
        other_major.id, title="Other Major Minor", position=1, start=datetime(2026, 9, 10, 8, 0)
    )

    response = client.post(
        "/minor_stage/swap-minor-stages",
        json=_swap_payload((route_graph_data["minor_stage_id"], 2), (other_minor.id, 1)),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_swap_minor_stages_flush_error_returns_500(client, auth_header, route_graph_data, monkeypatch):
    """A database error during the swap is reported as 500."""
    second_id = _create_minor_stage(route_graph_data["major_stage_id"]).id
    monkeypatch.setattr(f"{ROUTES}.db.session.flush", raise_error)

    response = client.post(
        "/minor_stage/swap-minor-stages",
        json=_swap_payload((route_graph_data["minor_stage_id"], 2), (second_id, 1)),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
