from datetime import datetime

from app.models import (
    Activity,
    CustomCountry,
    Journey,
    JourneysCustomCountriesLink,
    MajorStage,
    Medium,
    MinorStage,
    PlaceToVisit,
)
from db import db


def field(value):
    """
    Creates the form-field structure used by the TravelBuddy frontend.
    """
    return {
        "value": value,
        "errors": [],
        "isValid": True,
    }


# ---------------------------------------------------------------------------
# 1. Updating one journey must not delete stages / country links
#    belonging to another journey.
# ---------------------------------------------------------------------------

def test_removing_country_only_affects_current_journey(
    client,
    auth_header,
    ownership_data,
    monkeypatch,
):
    user_id = ownership_data["user_a_id"]
    journey_a_id = ownership_data["journey_a_id"]
    major_a_id = ownership_data["major_a_id"]

    # Use future dates so this test is independent of the old fixture dates.
    start = datetime(2027, 10, 1, 8, 0)
    end = datetime(2027, 10, 10, 20, 0)

    journey_a = db.session.get(Journey, journey_a_id)
    major_a = db.session.get(MajorStage, major_a_id)

    journey_a.scheduled_start_time = start
    journey_a.scheduled_end_time = end
    major_a.scheduled_start_time = start
    major_a.scheduled_end_time = end
    major_a.country = "Germany"
    journey_a.countries = "Germany"

    # Create another journey of the SAME user that also contains Germany.
    other_journey = Journey(
        name="Second Germany Journey",
        description="Must not be modified",
        scheduled_start_time=start,
        scheduled_end_time=end,
        countries="Germany",
        user_id=user_id,
    )

    db.session.add(other_journey)
    db.session.flush()

    other_stage = MajorStage(
        title="Protected Germany Stage",
        scheduled_start_time=start,
        scheduled_end_time=end,
        additional_info=None,
        country="Germany",
        position=0,
        journey_id=other_journey.id,
    )

    db.session.add(other_stage)

    # Both journeys use the same CustomCountry object.
    germany = CustomCountry(
        name="Germany",
        user_id=user_id,
    )

    france = CustomCountry(
        name="France",
        user_id=user_id,
    )

    db.session.add_all([germany, france])
    db.session.flush()

    db.session.add_all([
        JourneysCustomCountriesLink(
            journey_id=journey_a.id,
            custom_country_id=germany.id,
        ),
        JourneysCustomCountriesLink(
            journey_id=other_journey.id,
            custom_country_id=germany.id,
        ),
    ])

    db.session.commit()

    other_stage_id = other_stage.id
    other_journey_id = other_journey.id
    germany_id = germany.id

    # This test is about ownership/scoping, not JourneyValidation.
    # Therefore validation is stubbed out.
    monkeypatch.setattr(
        "app.routes.journey_routes."
        "JourneyValidation.validate_journey_update",
        lambda journey, *args, **kwargs: (journey, True),
    )

    payload = {
        "name": field("Journey User A"),
        "description": field("Updated"),
        "scheduled_start_time": field("01.10.2027"),
        "scheduled_end_time": field("10.10.2027"),
        "countries": field("France"),
        "budget": field(1000),
        "spent_money": field(0),
    }

    response = client.post(
        f"/journey/update-journey/{journey_a_id}",
        json=payload,
        headers=auth_header(user_id),
    )

    assert response.status_code == 200

    db.session.expire_all()

    # The Germany stage of the journey being updated SHOULD disappear.
    assert db.session.get(MajorStage, major_a_id) is None

    # The Germany stage belonging to the other journey MUST survive.
    assert db.session.get(MajorStage, other_stage_id) is not None

    # The Germany link for Journey A should be gone.
    own_link = db.session.execute(
        db.select(JourneysCustomCountriesLink).where(
            JourneysCustomCountriesLink.journey_id == journey_a_id,
            JourneysCustomCountriesLink.custom_country_id == germany_id,
        )
    ).scalar_one_or_none()

    assert own_link is None

    # The same country link belonging to the second journey MUST survive.
    protected_link = db.session.execute(
        db.select(JourneysCustomCountriesLink).where(
            JourneysCustomCountriesLink.journey_id == other_journey_id,
            JourneysCustomCountriesLink.custom_country_id == germany_id,
        )
    ).scalar_one_or_none()

    assert protected_link is not None


# ---------------------------------------------------------------------------
# 2. A user must not be able to reorder another user's MinorStage.
# ---------------------------------------------------------------------------

def test_user_cannot_reorder_foreign_minor_stage(
    client,
    auth_header,
    ownership_data,
):
    user_a_id = ownership_data["user_a_id"]

    minor_a_id = ownership_data["minor_a_id"]
    minor_b_id = ownership_data["minor_b_id"]

    minor_a = db.session.get(MinorStage, minor_a_id)
    minor_b = db.session.get(MinorStage, minor_b_id)

    minor_a.position = 0
    minor_b.position = 5

    db.session.commit()

    response = client.post(
        "/minor_stage/swap-minor-stages",
        json={
            "stagesPositionList": [
                {
                    "id": minor_a_id,
                    "position": 10,
                },
                {
                    # This stage belongs to User B.
                    "id": minor_b_id,
                    "position": 11,
                },
            ]
        },
        headers=auth_header(user_a_id),
    )

    assert response.status_code == 404

    db.session.expire_all()

    # Nothing should have been partially updated.
    assert db.session.get(MinorStage, minor_a_id).position == 0
    assert db.session.get(MinorStage, minor_b_id).position == 5


# ---------------------------------------------------------------------------
# 3. A Medium owned by User A must not be linked to User B's MinorStage.
# ---------------------------------------------------------------------------

def test_user_cannot_attach_medium_to_foreign_minor_stage(
    client,
    auth_header,
    ownership_data,
):
    user_a_id = ownership_data["user_a_id"]

    medium_a_id = ownership_data["medium_a_id"]
    foreign_minor_id = ownership_data["minor_b_id"]

    medium = db.session.get(Medium, medium_a_id)

    assert medium.user_id == user_a_id
    assert medium.minor_stage_id is None

    payload = {
        "favorite": field(False),
        "latitude": field(None),
        "longitude": field(None),
        "timestamp": field("03.09.2026 14:00"),
        "description": field("Updated description"),
        "minorStageId": field(foreign_minor_id),
        "placeToVisitId": field(None),
    }

    response = client.post(
        f"/medium/update-medium/{medium_a_id}",
        json=payload,
        headers=auth_header(user_a_id),
    )

    assert response.status_code == 404

    db.session.expire_all()

    medium = db.session.get(Medium, medium_a_id)

    # The relationship must not have changed.
    assert medium.minor_stage_id is None


# ---------------------------------------------------------------------------
# 4. An Activity must not be updated through a different MinorStage,
#    even if both resources belong to the same user.
# ---------------------------------------------------------------------------

def test_activity_cannot_be_updated_through_different_minor_stage(
    client,
    auth_header,
    ownership_data,
):
    user_a_id = ownership_data["user_a_id"]

    activity_id = ownership_data["activity_a_id"]
    major_stage_id = ownership_data["major_a_id"]

    activity = db.session.get(Activity, activity_id)
    original_name = activity.name

    # Create another MinorStage that ALSO belongs to User A.
    other_minor_stage = MinorStage(
        title="Another User A Stage",
        scheduled_start_time=datetime(2026, 9, 2, 8, 0),
        scheduled_end_time=datetime(2026, 9, 3, 20, 0),
        position=1,
        major_stage_id=major_stage_id,
    )

    db.session.add(other_minor_stage)
    db.session.commit()

    other_minor_id = other_minor_stage.id

    assert activity.minor_stage_id != other_minor_id

    payload = {
        "name": field("Illegally Updated Activity"),
        "description": field("Should never be applied"),
        "place": field("Munich"),
        "costs": field(15),
        "latitude": field(None),
        "longitude": field(None),
        "link": field(""),
        "booked": field(False),
    }

    response = client.post(
        (
            f"/activity/update-activity/"
            f"{other_minor_id}/{activity_id}"
        ),
        json=payload,
        headers=auth_header(user_a_id),
    )

    assert response.status_code == 404

    db.session.expire_all()

    activity = db.session.get(Activity, activity_id)

    # The Activity must still belong to its original MinorStage
    # and must not have been modified.
    assert activity.minor_stage_id != other_minor_id
    assert activity.name == original_name


# ---------------------------------------------------------------------------
# 5. User A must not create a Place using User B's CustomCountry.
# ---------------------------------------------------------------------------

def test_user_cannot_create_place_for_foreign_country(
    client,
    auth_header,
    ownership_data,
):
    user_a_id = ownership_data["user_a_id"]
    user_b_id = ownership_data["user_b_id"]

    foreign_country = CustomCountry(
        name="Foreign Country",
        user_id=user_b_id,
    )

    db.session.add(foreign_country)
    db.session.commit()

    foreign_country_id = foreign_country.id

    payload = {
        "countryId": field(foreign_country_id),
        "name": field("Forbidden Place"),
        "description": field("Should not be created"),
        "visited": field(False),
        "favorite": field(False),
        "latitude": field(48.137),
        "longitude": field(11.575),
        "link": field(""),
    }

    response = client.post(
        "/place-to-visit/create-place",
        json=payload,
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