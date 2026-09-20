from datetime import datetime, timedelta, timezone

import jwt
import pytest

# Important: ensures all SQLAlchemy models are registered
import app.models
from app.models import (
    Activity,
    Costs,
    Currency,
    CustomCountry,
    Journey,
    MajorStage,
    Medium,
    MinorStage,
    PlaceToVisit,
    Spendings,
    Transportation,
    User,
)
from db import db
from server import create_app

TEST_SECRET_KEY = "travelbuddy-test-secret-key"


@pytest.fixture()
def app(tmp_path):
    database_file = tmp_path / "travelbuddy_test.db"

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": TEST_SECRET_KEY,
        "SQLALCHEMY_DATABASE_URI": (
            f"sqlite:///{database_file.as_posix()}"
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    context = app.app_context()
    context.push()

    db.create_all()

    yield app

    db.session.remove()
    db.drop_all()

    context.pop()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_header(app):
    """
    Creates an Authorization header for a given user id.
    """

    def create_header(user_id):
        token = jwt.encode(
            {
                "user_id": user_id,
                "username": f"test-user-{user_id}",
                "type": "access",
                "exp": datetime.now(timezone.utc)
                + timedelta(hours=1),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return {
            "Authorization": f"Bearer {token}"
        }

    return create_header
  
@pytest.fixture()
def ownership_data(app):
    with app.app_context():
        start = datetime(2026, 9, 1, 8, 0)
        end = datetime(2026, 9, 10, 20, 0)

        # --------------------------------------------------
        # Users
        # --------------------------------------------------

        user_a = User(
            username="user_a",
            email="user_a@example.com",
            password="test-password-a",
        )

        user_b = User(
            username="user_b",
            email="user_b@example.com",
            password="test-password-b",
        )

        db.session.add_all([
            user_a,
            user_b,
        ])

        db.session.flush()

        # --------------------------------------------------
        # Journeys
        # --------------------------------------------------

        journey_a = Journey(
            name="Journey User A",
            description="Journey owned by User A",
            scheduled_start_time=start,
            scheduled_end_time=None,
            duration_days=(end - start).days if end else None,
            countries="Germany",
            user_id=user_a.id,
        )

        journey_b = Journey(
            name="Journey User B",
            description="Journey owned by User B",
            scheduled_start_time=start,
            scheduled_end_time=None,
            duration_days=(end - start).days if end else None,
            countries="Thailand",
            user_id=user_b.id,
        )

        db.session.add_all([
            journey_a,
            journey_b,
        ])

        db.session.flush()

        # --------------------------------------------------
        # Major stages
        # --------------------------------------------------

        major_a = MajorStage(
            title="Major Stage A",
            scheduled_start_time=start,
            scheduled_end_time=None,
            duration_days=(end - start).days if end else None,
            additional_info=None,
            country="Germany",
            position=0,
            journey_id=journey_a.id,
        )

        major_b = MajorStage(
            title="Major Stage B",
            scheduled_start_time=start,
            scheduled_end_time=None,
            duration_days=(end - start).days if end else None,
            additional_info=None,
            country="Thailand",
            position=0,
            journey_id=journey_b.id,
        )

        db.session.add_all([
            major_a,
            major_b,
        ])

        db.session.flush()

        # --------------------------------------------------
        # Minor stages
        # --------------------------------------------------

        minor_a = MinorStage(
            title="Minor Stage A",
            scheduled_start_time=start,
            scheduled_end_time=None,
            duration_days=(end - start).days if end else None,
            position=0,
            major_stage_id=major_a.id,
        )

        minor_b = MinorStage(
            title="Minor Stage B",
            scheduled_start_time=start,
            scheduled_end_time=None,
            duration_days=(end - start).days if end else None,
            position=0,
            major_stage_id=major_b.id,
        )

        db.session.add_all([
            minor_a,
            minor_b,
        ])

        db.session.flush()

        # --------------------------------------------------
        # Activities
        # --------------------------------------------------

        activity_a = Activity(
            name="Activity A",
            description="Activity owned by User A",
            costs=10.0,
            booked=False,
            place="Munich",
            latitude=None,
            longitude=None,
            link=None,
            minor_stage_id=minor_a.id,
        )

        activity_b = Activity(
            name="Activity B",
            description="Activity owned by User B",
            costs=20.0,
            booked=False,
            place="Bangkok",
            latitude=None,
            longitude=None,
            link=None,
            minor_stage_id=minor_b.id,
        )

        db.session.add_all([
            activity_a,
            activity_b,
        ])

        # --------------------------------------------------
        # Media
        # --------------------------------------------------

        medium_a = Medium(
            medium_type="image",
            url="https://example.com/user-a.jpg",
            thumbnail_url=None,
            favorite=False,
            latitude=None,
            longitude=None,
            timestamp=start,
            description="User A image",
            duration=None,
            user_id=user_a.id,
            storage_type="local",
            asset_id="123"
        )

        medium_b = Medium(
            medium_type="image",
            url="https://example.com/user-b.jpg",
            thumbnail_url=None,
            favorite=False,
            latitude=None,
            longitude=None,
            timestamp=start,
            description="User B image",
            duration=None,
            user_id=user_b.id,
            storage_type="local",
            asset_id="125"
        )

        db.session.add_all([
            medium_a,
            medium_b,
        ])

        db.session.commit()

        return {
            "user_a_id": user_a.id,
            "user_b_id": user_b.id,

            "journey_a_id": journey_a.id,
            "journey_b_id": journey_b.id,

            "major_a_id": major_a.id,
            "major_b_id": major_b.id,

            "minor_a_id": minor_a.id,
            "minor_b_id": minor_b.id,

            "activity_a_id": activity_a.id,
            "activity_b_id": activity_b.id,

            "medium_a_id": medium_a.id,
            "medium_b_id": medium_b.id,
        }


@pytest.fixture()
def field():
    def _make(value):
        return {
            "value": value,
            "errors": [],
            "isValid": True,
        }

    return _make


@pytest.fixture()
def route_graph_data(app):
    with app.app_context():
        start = datetime(2026, 9, 1, 8, 0)
        end = datetime(2026, 9, 10, 20, 0)

        user = User(
            username="routes_user",
            email="routes_user@example.com",
            password="StrongPwd1!",
        )
        db.session.add(user)
        db.session.flush()

        journey = Journey(
            name="Routes Journey",
            description="Route tests",
            scheduled_start_time=start,
            scheduled_end_time=end,
            duration_days=9,
            countries="Germany, France",
            user_id=user.id,
        )
        db.session.add(journey)
        db.session.flush()

        journey_costs = Costs(
            journey_id=journey.id,
            budget=5000,
            spent_money=0,
            money_exceeded=False,
        )
        db.session.add(journey_costs)

        major_stage = MajorStage(
            title="Germany",
            scheduled_start_time=start,
            scheduled_end_time=end,
            duration_days=9,
            additional_info="",
            country="Germany",
            position=1,
            journey_id=journey.id,
        )
        db.session.add(major_stage)
        db.session.flush()

        major_costs = Costs(
            major_stage_id=major_stage.id,
            budget=2000,
            spent_money=0,
            money_exceeded=False,
        )
        db.session.add(major_costs)

        minor_stage = MinorStage(
            title="Berlin",
            scheduled_start_time=start,
            scheduled_end_time=end,
            duration_days=3,
            position=1,
            major_stage_id=major_stage.id,
        )
        db.session.add(minor_stage)
        db.session.flush()

        minor_costs = Costs(
            minor_stage_id=minor_stage.id,
            budget=700,
            spent_money=0,
            money_exceeded=False,
        )
        db.session.add(minor_costs)

        custom_country = CustomCountry(
            name="Germany",
            currencies="EUR",
            languages="German",
            capital="Berlin",
            population=100,
            region="Europe",
            subregion="Western Europe",
            wiki_link="https://example.com",
            visited=False,
            visum_regulations=None,
            best_time_to_visit=None,
            general_information=None,
            user_id=user.id,
        )
        db.session.add(custom_country)
        db.session.flush()

        place = PlaceToVisit(
            name="Brandenburg Gate",
            description="Landmark",
            visited=False,
            favorite=False,
            latitude=52.5,
            longitude=13.4,
            link="",
            user_id=user.id,
            custom_country_id=custom_country.id,
        )
        db.session.add(place)
        db.session.flush()

        activity = Activity(
            name="Museum",
            description="Visit",
            costs=20,
            booked=False,
            place="Berlin",
            latitude=None,
            longitude=None,
            link="",
            minor_stage_id=minor_stage.id,
        )
        db.session.add(activity)

        spending = Spendings(
            name="Lunch",
            amount=15,
            date=start,
            category="Dine out",
            costs_id=minor_costs.id,
        )
        db.session.add(spending)

        transportation_major = Transportation(
            type="Train",
            start_time=start,
            arrival_time=start + timedelta(hours=2),
            place_of_departure="A",
            departure_latitude=None,
            departure_longitude=None,
            place_of_arrival="B",
            arrival_latitude=None,
            arrival_longitude=None,
            transportation_costs=100,
            link="",
            major_stage_id=major_stage.id,
        )
        db.session.add(transportation_major)

        medium = Medium(
            medium_type="image",
            url="https://example.com/img.jpg",
            thumbnail_url=None,
            favorite=False,
            latitude=None,
            longitude=None,
            timestamp=start,
            description="desc",
            duration=None,
            user_id=user.id,
            storage_type="local",
            asset_id="asset-1",
            minor_stage_id=minor_stage.id,
            place_to_visit_id=place.id,
        )
        db.session.add(medium)

        currency = Currency(
            code="EUR",
            name="Euro",
            symbol="€",
            conversion_rate=1.0,
            user_id=user.id,
        )
        db.session.add(currency)

        db.session.commit()

        return {
            "user_id": user.id,
            "journey_id": journey.id,
            "major_stage_id": major_stage.id,
            "minor_stage_id": minor_stage.id,
            "custom_country_id": custom_country.id,
            "place_id": place.id,
            "activity_id": activity.id,
            "spending_id": spending.id,
            "medium_id": medium.id,
            "transportation_major_id": transportation_major.id,
            "currency_id": currency.id,
        }