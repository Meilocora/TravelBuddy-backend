from datetime import datetime, timedelta

from app.models import Accommodation, Costs, Journey, MajorStage, MinorStage, User
from db import db


def _field(value):
    return {"value": value, "isValid": True, "errors": []}


def _payload(**overrides):
    tomorrow = datetime.now() + timedelta(days=1)
    values = {
        "title": "Updated stop",
        "scheduled_start_time": tomorrow.strftime("%d.%m.%Y"),
        "scheduled_end_time": (tomorrow + timedelta(days=1)).strftime(
            "%d.%m.%Y"
        ),
        "duration_days": 1,
        "budget": 400,
        "spent_money": 0,
        "position": 1,
        "accommodation_place": "New Hotel",
        "accommodation_costs": 120,
        "accommodation_booked": True,
        "accommodation_latitude": 48.137154,
        "accommodation_longitude": 11.576124,
        "accommodation_link": "",
    }
    values.update(overrides)
    return {key: _field(value) for key, value in values.items()}


def _create_update_data():
    start = datetime(2026, 9, 1)
    end = datetime(2026, 9, 10)
    user = User(
        username="minor-stage-user",
        email="minor-stage@example.com",
        password="password",
    )
    journey = Journey(
        name="Minor stage update journey",
        description="",
        scheduled_start_time=start,
        scheduled_end_time=end,
        duration_days=(end - start).days if end else None,
        countries="Germany",
        user=user,
    )
    major_stage = MajorStage(
        title="Germany",
        scheduled_start_time=start,
        scheduled_end_time=end,
        duration_days=(end - start).days if end else None,
        additional_info=None,
        country="Germany",
        position=1,
        journey=journey,
    )
    minor_stage = MinorStage(
        title="Old stop",
        scheduled_start_time=start,
        scheduled_end_time=end,
        duration_days=(end - start).days if end else None,
        position=1,
        major_stage=major_stage,
    )
    db.session.add_all([
        user,
        journey,
        major_stage,
        minor_stage,
    ])
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


def test_update_minor_stage_updates_accommodation_and_coordinates(
    client,
    auth_header,
):
    user_id, major_stage_id, minor_stage_id = _create_update_data()

    response = client.post(
        f"/minor_stage/update-minor-stage/{major_stage_id}/{minor_stage_id}",
        json=_payload(),
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

def test_update_rolls_back_when_cost_recalculation_fails(
    client,
    auth_header,
    monkeypatch,
):
    user_id, major_stage_id, minor_stage_id = _create_update_data()

    def fail_recalculation(_journey_costs):
        raise RuntimeError("recalculation failed")

    monkeypatch.setattr(
        "app.routes.minor_stage_routes.calculate_journey_costs",
        fail_recalculation,
    )

    response = client.post(
        f"/minor_stage/update-minor-stage/{major_stage_id}/{minor_stage_id}",
        json=_payload(),
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
