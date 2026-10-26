"""
Tests for the transportation endpoints (``/transportation``).

Transportation can be attached to a major stage or to a minor stage. Both
variants expose identical endpoints, so every test runs once per stage level
via the parametrized ``stage`` fixture:

    /transportation/create-<level>-stage-transportation/<stage_id>
    /transportation/update-<level>-stage-transportation/<stage_id>/<transportation_id>
    /transportation/delete-<level>-stage-transportation/<stage_id>
"""

from dataclasses import dataclass
from datetime import datetime

import pytest
from helpers import field, raise_error, stub_validation

from app.models import Transportation
from db import db

ROUTES = "app.routes.transportation_routes"
VALIDATE_TRANSPORTATION = f"{ROUTES}.TransportationValidation.validate_transportation"


@dataclass
class StageUnderTest:
    """A stage level together with the ids of a stage and its transportation."""

    level: str
    stage_id: int
    transportation_id: int

    def create_url(self, stage_id=None):
        return f"/transportation/create-{self.level}-stage-transportation/{stage_id or self.stage_id}"

    def update_url(self, stage_id=None, transportation_id=None):
        return (
            f"/transportation/update-{self.level}-stage-transportation/"
            f"{stage_id or self.stage_id}/{transportation_id or self.transportation_id}"
        )

    def delete_url(self, stage_id=None):
        return f"/transportation/delete-{self.level}-stage-transportation/{stage_id or self.stage_id}"


@pytest.fixture(params=["major", "minor"])
def stage(request, route_graph_data):
    """
    Provides the major stage or the minor stage of ``route_graph_data`` with
    an existing transportation. The major stage already has one from the
    fixture; for the minor stage one is created here.
    """
    if request.param == "major":
        return StageUnderTest(
            "major",
            route_graph_data["major_stage_id"],
            route_graph_data["transportation_major_id"],
        )

    transportation = Transportation(
        type="Train",
        start_time=datetime(2026, 9, 1, 10, 0),
        arrival_time=datetime(2026, 9, 1, 12, 0),
        place_of_departure="A",
        departure_latitude=None,
        departure_longitude=None,
        place_of_arrival="B",
        arrival_latitude=None,
        arrival_longitude=None,
        transportation_costs=40,
        link="",
        minor_stage_id=route_graph_data["minor_stage_id"],
    )
    db.session.add(transportation)
    db.session.commit()
    return StageUnderTest("minor", route_graph_data["minor_stage_id"], transportation.id)


@pytest.fixture()
def headers(auth_header, route_graph_data):
    """Authorization header of the ``route_graph_data`` user."""
    return auth_header(route_graph_data["user_id"])


def _transport_payload():
    """Builds a complete transportation form as sent by the frontend."""
    return {
        "type": field("Train"),
        "start_time": field("01.09.2026 10:00"),
        "arrival_time": field("01.09.2026 12:00"),
        "place_of_departure": field("A"),
        "departure_latitude": field(None),
        "departure_longitude": field(None),
        "place_of_arrival": field("B"),
        "arrival_latitude": field(None),
        "arrival_longitude": field(None),
        "transportation_costs": field(50),
        "link": field(""),
    }


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_transportation_success(client, headers, stage, monkeypatch):
    """A valid transportation is created for the stage."""
    monkeypatch.setattr(VALIDATE_TRANSPORTATION, stub_validation(True))

    response = client.post(stage.create_url(), json=_transport_payload(), headers=headers)

    assert response.status_code == 201


def test_create_transportation_stage_not_found(client, headers, stage):
    """Creating a transportation for an unknown stage returns 404."""
    response = client.post(stage.create_url(999999), json=_transport_payload(), headers=headers)

    assert response.status_code == 404


def test_create_transportation_validation_fail(client, headers, stage, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_TRANSPORTATION, stub_validation(False))

    response = client.post(stage.create_url(), json=_transport_payload(), headers=headers)

    assert response.status_code == 400


def test_create_transportation_commit_error_returns_500(client, headers, stage, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_TRANSPORTATION, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(stage.create_url(), json=_transport_payload(), headers=headers)

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_transportation_success(client, headers, stage, monkeypatch):
    """
    A valid update is applied to the stage's transportation.

    Note: the update endpoints answer with 201 (not 200) on success.
    """
    monkeypatch.setattr(VALIDATE_TRANSPORTATION, stub_validation(True))

    response = client.post(stage.update_url(), json=_transport_payload(), headers=headers)

    assert response.status_code == 201
    db.session.expire_all()
    assert db.session.get(Transportation, stage.transportation_id).transportation_costs == 50


def test_update_transportation_not_found(client, headers, stage):
    """Updating an unknown transportation returns 404."""
    response = client.post(
        stage.update_url(transportation_id=999999),
        json=_transport_payload(),
        headers=headers,
    )

    assert response.status_code == 404


def test_update_transportation_stage_not_found(client, headers, stage):
    """Updating through an unknown stage returns 404."""
    response = client.post(
        stage.update_url(stage_id=999999, transportation_id=999999),
        json=_transport_payload(),
        headers=headers,
    )

    assert response.status_code == 404


def test_update_transportation_validation_fail(client, headers, stage, monkeypatch):
    """Invalid form values are rejected with 400."""
    monkeypatch.setattr(VALIDATE_TRANSPORTATION, stub_validation(False))

    response = client.post(stage.update_url(), json=_transport_payload(), headers=headers)

    assert response.status_code == 400


def test_update_transportation_commit_error_returns_500(client, headers, stage, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(VALIDATE_TRANSPORTATION, stub_validation(True))
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.post(stage.update_url(), json=_transport_payload(), headers=headers)

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_transportation_success(client, headers, stage):
    """Deleting removes the stage's transportation."""
    response = client.delete(stage.delete_url(), headers=headers)

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Transportation, stage.transportation_id) is None


def test_delete_transportation_stage_not_found(client, headers, stage):
    """Deleting the transportation of an unknown stage returns 404."""
    response = client.delete(stage.delete_url(999999), headers=headers)

    assert response.status_code == 404


def test_delete_transportation_commit_error_returns_500(client, headers, stage, monkeypatch):
    """A failing database commit is reported as 500."""
    monkeypatch.setattr(f"{ROUTES}.db.session.commit", raise_error)

    response = client.delete(stage.delete_url(), headers=headers)

    assert response.status_code == 500
