"""
Shared pytest fixtures for the TravelBuddy backend.

The Flask app is created once per test session, because building it is the
most expensive part of the setup (Werkzeug compiles ~550 URL rules). The
database schema, on the other hand, is created and dropped for every single
test, so each test still starts with an empty in-memory SQLite database and
tests stay fully isolated from each other. No test ever touches a development
or production database.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy.pool import StaticPool

# Importing the models module registers every model with SQLAlchemy,
# which is required before ``db.create_all()`` can build the schema.
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

TEST_SECRET_KEY = "travelbuddy-test-secret-key-for-hs256-and-hs512-tokens-0123456789"

START = datetime(2026, 9, 1, 8, 0)
END = datetime(2026, 9, 10, 20, 0)


# ---------------------------------------------------------------------------
# Application, client and authentication
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def flask_app():
    """
    Creates the Flask app once for the whole test session.

    ``create_app()`` takes ~0.1 s, almost all of it spent registering the
    blueprints' URL rules. Doing that for each of the ~200 tests used to cost
    about 20 s. Sharing one app is safe, because the tests only read
    ``app.config`` and never modify the app itself. All per-test state lives
    in the database, which the ``app`` fixture below resets for every test.

    Tests should not use this fixture directly; use ``app`` instead.
    """
    # The built-in ``monkeypatch`` fixture is function-scoped and therefore
    # cannot be used by a session-scoped fixture (pytest raises ScopeMismatch).
    # ``MonkeyPatch.context()`` is the session-safe equivalent: the patch stays
    # active until the ``with`` block ends, i.e. after the last test, and is
    # undone automatically afterwards.
    with pytest.MonkeyPatch.context() as mp:
        # auth_routes reads SECRET_KEY from the environment at import time,
        # while the token check uses app.config. Align both for all tests.
        mp.setattr("app.routes.auth_routes.SECRET_KEY", TEST_SECRET_KEY)

        yield create_app({
            "TESTING": True,
            "SECRET_KEY": TEST_SECRET_KEY,
            # "sqlite://" without a file path means: in-memory database.
            # Nothing is written to disk, which makes setup/teardown fast.
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                # An in-memory SQLite database only exists inside the single
                # connection that created it; every new connection would get
                # its own, empty database. SQLAlchemy's default pool may open
                # several connections, so the tables created by
                # ``db.create_all()`` could be missing in the connection a
                # request later uses. ``StaticPool`` always hands out the same
                # one connection, so the fixtures, the test code and the
                # requests sent through the test client all share one database.
                "poolclass": StaticPool,
                # SQLite refuses by default to use a connection in a thread
                # other than the one that created it. Because StaticPool reuses
                # the one connection everywhere, this check must be disabled.
                "connect_args": {"check_same_thread": False},
            },
        })


@pytest.fixture()
def app(flask_app):
    """
    Provides the shared Flask app with a fresh, empty database for one test.

    Runs for every test (function scope): it creates all tables before the
    test and drops them afterwards, so no data leaks from one test into the
    next. With an in-memory database this takes only a few milliseconds.

    The app context stays pushed for the whole test, which allows tests and
    data fixtures to query ``db.session`` directly. A new context per test
    also gives every test its own ``flask.g``.
    """
    context = flask_app.app_context()
    context.push()
    db.create_all()

    yield flask_app

    # Discard the session (and with it any uncommitted transaction, e.g. from
    # a test that simulated a failing commit) before dropping the tables.
    db.session.remove()
    db.drop_all()
    context.pop()


@pytest.fixture()
def client(app):
    """Flask test client for issuing HTTP requests against the app."""
    return app.test_client()


@pytest.fixture()
def auth_header(app):
    """
    Factory that builds a valid ``Authorization`` header for a user id.

    The token is signed with the test secret and mirrors the claims of a real
    access token, so protected routes resolve ``current_user`` from it.
    """

    def create_header(user_id):
        token = jwt.encode(
            {
                "user_id": user_id,
                "username": f"test-user-{user_id}",
                "type": "access",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    return create_header


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------


def _create_owned_graph(suffix, country, place):
    """
    Creates a minimal resource tree for one user:
    User -> Journey -> MajorStage -> MinorStage -> Activity, plus one Medium.

    The medium is intentionally not linked to the minor stage, so tests can
    check whether linking it to a foreign stage is rejected.
    """
    duration_days = (END - START).days

    user = User(
        username=f"user_{suffix}",
        email=f"user_{suffix}@example.com",
        password=f"test-password-{suffix}",
    )
    db.session.add(user)
    db.session.flush()

    journey = Journey(
        name=f"Journey User {suffix.upper()}",
        description=f"Journey owned by User {suffix.upper()}",
        scheduled_start_time=START,
        scheduled_end_time=None,
        duration_days=duration_days,
        countries=country,
        user_id=user.id,
    )
    db.session.add(journey)
    db.session.flush()

    major_stage = MajorStage(
        title=f"Major Stage {suffix.upper()}",
        scheduled_start_time=START,
        scheduled_end_time=None,
        duration_days=duration_days,
        additional_info=None,
        country=country,
        position=0,
        journey_id=journey.id,
    )
    db.session.add(major_stage)
    db.session.flush()

    minor_stage = MinorStage(
        title=f"Minor Stage {suffix.upper()}",
        scheduled_start_time=START,
        scheduled_end_time=None,
        duration_days=duration_days,
        position=0,
        major_stage_id=major_stage.id,
    )
    db.session.add(minor_stage)
    db.session.flush()

    activity = Activity(
        name=f"Activity {suffix.upper()}",
        description=f"Activity owned by User {suffix.upper()}",
        costs=10.0,
        booked=False,
        place=place,
        latitude=None,
        longitude=None,
        link=None,
        minor_stage_id=minor_stage.id,
    )
    medium = Medium(
        medium_type="image",
        url=f"https://example.com/user-{suffix}.jpg",
        thumbnail_url=None,
        favorite=False,
        latitude=None,
        longitude=None,
        timestamp=START,
        description=f"User {suffix.upper()} image",
        duration=None,
        user_id=user.id,
        storage_type="local",
        asset_id=f"asset-{suffix}",
    )
    db.session.add_all([activity, medium])
    db.session.flush()

    return {
        f"user_{suffix}_id": user.id,
        f"journey_{suffix}_id": journey.id,
        f"major_{suffix}_id": major_stage.id,
        f"minor_{suffix}_id": minor_stage.id,
        f"activity_{suffix}_id": activity.id,
        f"medium_{suffix}_id": medium.id,
    }


@pytest.fixture()
def ownership_data(app):
    """
    Two users (A and B), each owning an identical resource tree.

    Used by authorization tests: requests are issued as User A against
    resources of User B, which must be treated as non-existent.

    Returns a dict of ids, e.g. ``user_a_id``, ``journey_b_id``, ``minor_a_id``.
    """
    data = {
        **_create_owned_graph("a", country="Germany", place="Munich"),
        **_create_owned_graph("b", country="Thailand", place="Bangkok"),
    }
    db.session.commit()
    return data


@pytest.fixture()
def route_graph_data(app):
    """
    A single user with a fully populated journey, used by the route tests.

    Contains one of every resource type: journey, major stage and minor stage
    (each with costs), custom country, place to visit, activity, spending,
    major-stage transportation, medium and currency.

    Returns a dict of the created ids.
    """
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
        scheduled_start_time=START,
        scheduled_end_time=END,
        duration_days=9,
        countries="Germany, France",
        user_id=user.id,
    )
    db.session.add(journey)
    db.session.flush()

    major_stage = MajorStage(
        title="Germany",
        scheduled_start_time=START,
        scheduled_end_time=END,
        duration_days=9,
        additional_info="",
        country="Germany",
        position=1,
        journey_id=journey.id,
    )
    db.session.add(major_stage)
    db.session.flush()

    minor_stage = MinorStage(
        title="Berlin",
        scheduled_start_time=START,
        scheduled_end_time=END,
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
    db.session.add_all([
        Costs(journey_id=journey.id, budget=5000, spent_money=0, money_exceeded=False),
        Costs(major_stage_id=major_stage.id, budget=2000, spent_money=0, money_exceeded=False),
        minor_costs,
    ])

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
    spending = Spendings(
        name="Lunch",
        amount=15,
        date=START,
        category="Dine out",
        costs_id=minor_costs.id,
    )
    transportation_major = Transportation(
        type="Train",
        start_time=START,
        arrival_time=START + timedelta(hours=2),
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
    medium = Medium(
        medium_type="image",
        url="https://example.com/img.jpg",
        thumbnail_url=None,
        favorite=False,
        latitude=None,
        longitude=None,
        timestamp=START,
        description="desc",
        duration=None,
        user_id=user.id,
        storage_type="local",
        asset_id="asset-1",
        minor_stage_id=minor_stage.id,
        place_to_visit_id=place.id,
    )
    currency = Currency(
        code="EUR",
        name="Euro",
        symbol="€",
        conversion_rate=1.0,
        user_id=user.id,
    )
    db.session.add_all([activity, spending, transportation_major, medium, currency])
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
