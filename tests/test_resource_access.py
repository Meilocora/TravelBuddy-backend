from app.routes.resource_access import (
    get_user_journey,
    get_user_major_stage,
    get_user_minor_stage,
    get_user_activity,
    get_user_medium,
)


def test_user_can_access_own_journey(ownership_data):
    journey = get_user_journey(
        ownership_data["user_a_id"],
        ownership_data["journey_a_id"],
    )

    assert journey is not None
    assert journey.id == ownership_data["journey_a_id"]


def test_user_cannot_access_foreign_journey(ownership_data):
    journey = get_user_journey(
        ownership_data["user_a_id"],
        ownership_data["journey_b_id"],
    )

    assert journey is None


def test_user_cannot_access_foreign_major_stage(ownership_data):
    stage = get_user_major_stage(
        ownership_data["user_a_id"],
        ownership_data["major_b_id"],
    )

    assert stage is None


def test_user_cannot_access_foreign_minor_stage(ownership_data):
    stage = get_user_minor_stage(
        ownership_data["user_a_id"],
        ownership_data["minor_b_id"],
    )

    assert stage is None


def test_user_can_access_own_nested_activity(ownership_data):
    activity = get_user_activity(
        ownership_data["user_a_id"],
        ownership_data["activity_a_id"],
    )

    assert activity is not None


def test_user_cannot_access_foreign_nested_activity(ownership_data):
    activity = get_user_activity(
        ownership_data["user_a_id"],
        ownership_data["activity_b_id"],
    )

    assert activity is None


def test_user_can_access_own_medium(ownership_data):
    medium = get_user_medium(
        ownership_data["user_a_id"],
        ownership_data["medium_a_id"],
    )

    assert medium is not None


def test_user_cannot_access_foreign_medium(ownership_data):
    medium = get_user_medium(
        ownership_data["user_a_id"],
        ownership_data["medium_b_id"],
    )

    assert medium is None