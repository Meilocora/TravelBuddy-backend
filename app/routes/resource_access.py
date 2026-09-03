from sqlalchemy import or_

from db import db
from app.models import (
    Journey,
    CustomCountry,
    MajorStage,
    MinorStage,
    Costs,
    Spendings,
    Transportation,
    Accommodation,
    Activity,
    PlaceToVisit,
    Medium,
    Currency,
)


def _single_result(statement):
    """
    Execute a query that should return at most one resource.
    Returns None if the resource does not exist or does not belong to the user.
    """
    return db.session.execute(statement).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Directly user-owned resources
# ---------------------------------------------------------------------------

def get_user_journey(user_id: int, journey_id: int):
    return _single_result(
        db.select(Journey).where(
            Journey.id == journey_id,
            Journey.user_id == user_id,
        )
    )


def get_user_custom_country(user_id: int, country_id: int):
    return _single_result(
        db.select(CustomCountry).where(
            CustomCountry.id == country_id,
            CustomCountry.user_id == user_id,
        )
    )


def get_user_place(user_id: int, place_id: int):
    return _single_result(
        db.select(PlaceToVisit).where(
            PlaceToVisit.id == place_id,
            PlaceToVisit.user_id == user_id,
        )
    )


def get_user_medium(user_id: int, medium_id: int):
    return _single_result(
        db.select(Medium).where(
            Medium.id == medium_id,
            Medium.user_id == user_id,
        )
    )


def get_user_currency(user_id: int, currency_id: int):
    return _single_result(
        db.select(Currency).where(
            Currency.id == currency_id,
            Currency.user_id == user_id,
        )
    )


# ---------------------------------------------------------------------------
# Journey children
# ---------------------------------------------------------------------------

def get_user_major_stage(
    user_id: int,
    major_stage_id: int,
    journey_id: int | None = None,
):
    statement = db.select(MajorStage).where(
        MajorStage.id == major_stage_id,
        MajorStage.journey.has(
            Journey.user_id == user_id
        ),
    )

    if journey_id is not None:
        statement = statement.where(
            MajorStage.journey_id == journey_id
        )

    return _single_result(statement)


def get_user_minor_stage(
    user_id: int,
    minor_stage_id: int,
    major_stage_id: int | None = None,
):
    statement = db.select(MinorStage).where(
        MinorStage.id == minor_stage_id,
        MinorStage.major_stage.has(
            MajorStage.journey.has(
                Journey.user_id == user_id
            )
        ),
    )

    if major_stage_id is not None:
        statement = statement.where(
            MinorStage.major_stage_id == major_stage_id
        )

    return _single_result(statement)


# ---------------------------------------------------------------------------
# Minor-stage children
# ---------------------------------------------------------------------------

def get_user_activity(
    user_id: int,
    activity_id: int,
    minor_stage_id: int | None = None,
):
    statement = db.select(Activity).where(
        Activity.id == activity_id,
        Activity.minor_stage.has(
            MinorStage.major_stage.has(
                MajorStage.journey.has(
                    Journey.user_id == user_id
                )
            )
        ),
    )

    if minor_stage_id is not None:
        statement = statement.where(
            Activity.minor_stage_id == minor_stage_id
        )

    return _single_result(statement)


def get_user_accommodation(
    user_id: int,
    accommodation_id: int,
    minor_stage_id: int | None = None,
):
    statement = db.select(Accommodation).where(
        Accommodation.id == accommodation_id,
        Accommodation.minor_stage.has(
            MinorStage.major_stage.has(
                MajorStage.journey.has(
                    Journey.user_id == user_id
                )
            )
        ),
    )

    if minor_stage_id is not None:
        statement = statement.where(
            Accommodation.minor_stage_id == minor_stage_id
        )

    return _single_result(statement)


# ---------------------------------------------------------------------------
# Transportation
#
# Transportation can belong either directly to a MajorStage or to a MinorStage.
# ---------------------------------------------------------------------------

def get_user_transportation(user_id: int, transportation_id: int):
    return _single_result(
        db.select(Transportation).where(
            Transportation.id == transportation_id,
            or_(
                Transportation.major_stage.has(
                    MajorStage.journey.has(
                        Journey.user_id == user_id
                    )
                ),
                Transportation.minor_stage.has(
                    MinorStage.major_stage.has(
                        MajorStage.journey.has(
                            Journey.user_id == user_id
                        )
                    )
                ),
            ),
        )
    )


# ---------------------------------------------------------------------------
# Costs
#
# Costs can belong to Journey, MajorStage or MinorStage.
# ---------------------------------------------------------------------------

def _costs_belong_to_user(user_id: int):
    return or_(
        Costs.journey.has(
            Journey.user_id == user_id
        ),
        Costs.major_stage.has(
            MajorStage.journey.has(
                Journey.user_id == user_id
            )
        ),
        Costs.minor_stage.has(
            MinorStage.major_stage.has(
                MajorStage.journey.has(
                    Journey.user_id == user_id
                )
            )
        ),
    )


def get_user_costs(user_id: int, costs_id: int):
    return _single_result(
        db.select(Costs).where(
            Costs.id == costs_id,
            _costs_belong_to_user(user_id),
        )
    )


def get_user_spending(user_id: int, spending_id: int):
    return _single_result(
        db.select(Spendings).where(
            Spendings.id == spending_id,
            Spendings.costs.has(
                _costs_belong_to_user(user_id)
            ),
        )
    )


# ---------------------------------------------------------------------------
# Batch access
#
# Useful for endpoints such as stage reordering.
# ---------------------------------------------------------------------------

def get_user_major_stages_by_ids(user_id: int, stage_ids: list[int]):
    if not stage_ids:
        return []

    return db.session.execute(
        db.select(MajorStage).where(
            MajorStage.id.in_(stage_ids),
            MajorStage.journey.has(
                Journey.user_id == user_id
            ),
        )
    ).scalars().all()


def get_user_minor_stages_by_ids(user_id: int, stage_ids: list[int]):
    if not stage_ids:
        return []

    return db.session.execute(
        db.select(MinorStage).where(
            MinorStage.id.in_(stage_ids),
            MinorStage.major_stage.has(
                MajorStage.journey.has(
                    Journey.user_id == user_id
                )
            ),
        )
    ).scalars().all()