"""
Security regression tests for ownership boundaries.

Each test reproduces a scenario in which a user tries to read, change or
link resources across ownership boundaries. The request must be rejected
with 404 (foreign resources are treated as non-existent), and the database
must remain unchanged.
"""

from datetime import datetime

from helpers import field

from app.models import Activity, CustomCountry, Medium, MinorStage, PlaceToVisit
from db import db


def test_user_cannot_reorder_foreign_minor_stage(client, auth_header, ownership_data):
    """
    A swap request mixing an own and a foreign minor stage is rejected as a
    whole: neither stage may be repositioned, not even partially.
    """
    minor_a_id = ownership_data["minor_a_id"]
    minor_b_id = ownership_data["minor_b_id"]  # owned by User B

    db.session.get(MinorStage, minor_a_id).position = 0
    db.session.get(MinorStage, minor_b_id).position = 5
    db.session.commit()

    response = client.post(
        "/minor_stage/swap-minor-stages",
        json={
            "stagesPositionList": [
                {"id": minor_a_id, "position": 10},
                {"id": minor_b_id, "position": 11},
            ]
        },
        headers=auth_header(ownership_data["user_a_id"]),
    )

    assert response.status_code == 404
    db.session.expire_all()
    assert db.session.get(MinorStage, minor_a_id).position == 0
    assert db.session.get(MinorStage, minor_b_id).position == 5


def test_user_cannot_attach_medium_to_foreign_minor_stage(client, auth_header, ownership_data):
    """User A's medium must not be linkable to User B's minor stage."""
    user_a_id = ownership_data["user_a_id"]
    medium_a_id = ownership_data["medium_a_id"]

    medium = db.session.get(Medium, medium_a_id)
    assert medium.user_id == user_a_id
    assert medium.minor_stage_id is None

    response = client.post(
        f"/medium/update-medium/{medium_a_id}",
        json={
            "favorite": field(False),
            "latitude": field(None),
            "longitude": field(None),
            "timestamp": field("03.09.2026 14:00"),
            "description": field("Updated description"),
            "minorStageId": field(ownership_data["minor_b_id"]),
            "placeToVisitId": field(None),
        },
        headers=auth_header(user_a_id),
    )

    assert response.status_code == 404
    db.session.expire_all()
    assert db.session.get(Medium, medium_a_id).minor_stage_id is None


def test_activity_cannot_be_updated_through_different_minor_stage(client, auth_header, ownership_data):
    """
    An activity may only be updated through the minor stage it belongs to,
    even if the other minor stage is owned by the same user.

    This prevents moving or modifying child objects through an unrelated
    parent resource in the URL.
    """
    user_a_id = ownership_data["user_a_id"]
    activity_id = ownership_data["activity_a_id"]
    original_name = db.session.get(Activity, activity_id).name

    other_minor_stage = MinorStage(
        title="Another User A Stage",
        scheduled_start_time=datetime(2026, 9, 2, 8, 0),
        scheduled_end_time=datetime(2026, 9, 3, 20, 0),
        duration_days=1,
        position=1,
        major_stage_id=ownership_data["major_a_id"],
    )
    db.session.add(other_minor_stage)
    db.session.commit()
    other_minor_id = other_minor_stage.id

    response = client.post(
        f"/activity/update-activity/{other_minor_id}/{activity_id}",
        json={
            "name": field("Illegally Updated Activity"),
            "description": field("Should never be applied"),
            "place": field("Munich"),
            "costs": field(15),
            "latitude": field(None),
            "longitude": field(None),
            "link": field(""),
            "booked": field(False),
        },
        headers=auth_header(user_a_id),
    )

    assert response.status_code == 404
    db.session.expire_all()
    activity = db.session.get(Activity, activity_id)
    assert activity.minor_stage_id == ownership_data["minor_a_id"]
    assert activity.name == original_name


def test_user_cannot_create_place_for_foreign_country(client, auth_header, ownership_data):
    """User A must not create a place inside User B's custom country."""
    user_a_id = ownership_data["user_a_id"]

    foreign_country = CustomCountry(name="Foreign Country", user_id=ownership_data["user_b_id"])
    db.session.add(foreign_country)
    db.session.commit()
    foreign_country_id = foreign_country.id

    response = client.post(
        "/place-to-visit/create-place",
        json={
            "countryId": field(foreign_country_id),
            "name": field("Forbidden Place"),
            "description": field("Should not be created"),
            "visited": field(False),
            "favorite": field(False),
            "latitude": field(48.137),
            "longitude": field(11.575),
            "link": field(""),
        },
        headers=auth_header(user_a_id),
    )

    assert response.status_code == 404
    created_place = db.session.execute(
        db.select(PlaceToVisit).where(
            PlaceToVisit.user_id == user_a_id,
            PlaceToVisit.custom_country_id == foreign_country_id,
        )
    ).scalar_one_or_none()
    assert created_place is None
