from datetime import datetime, timedelta, timezone

import jwt
import pytest

from db import db
from server import create_app

# Important: ensures all SQLAlchemy models are registered
import app.models  # noqa: F401

from app.models import (
    User,
    Journey,
    MajorStage,
    MinorStage,
    Activity,
    Medium,
)


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
            scheduled_end_time=end,
            countries="Germany",
            user_id=user_a.id,
        )

        journey_b = Journey(
            name="Journey User B",
            description="Journey owned by User B",
            scheduled_start_time=start,
            scheduled_end_time=end,
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
            scheduled_end_time=end,
            additional_info=None,
            country="Germany",
            position=0,
            journey_id=journey_a.id,
        )

        major_b = MajorStage(
            title="Major Stage B",
            scheduled_start_time=start,
            scheduled_end_time=end,
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
            scheduled_end_time=end,
            position=0,
            major_stage_id=major_a.id,
        )

        minor_b = MinorStage(
            title="Minor Stage B",
            scheduled_start_time=start,
            scheduled_end_time=end,
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