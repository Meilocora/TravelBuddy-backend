from app.models import Journey, Medium
from db import db


def test_user_cannot_delete_foreign_journey(
    client,
    auth_header,
    ownership_data,
):
    response = client.delete(
        f"/journey/delete-journey/"
        f"{ownership_data['journey_b_id']}",
        headers=auth_header(
            ownership_data["user_a_id"]
        ),
    )

    assert response.status_code == 404

    journey = db.session.get(
        Journey,
        ownership_data["journey_b_id"],
    )

    assert journey is not None
    
def test_user_can_delete_own_journey(
    client,
    auth_header,
    ownership_data,
):
    journey_id = ownership_data["journey_a_id"]

    response = client.delete(
        f"/journey/delete-journey/{journey_id}",
        headers=auth_header(
            ownership_data["user_a_id"]
        ),
    )

    assert response.status_code == 200

    db.session.expire_all()

    journey = db.session.get(
        Journey,
        journey_id,
    )

    assert journey is None
    
def test_user_cannot_delete_foreign_medium(
    client,
    auth_header,
    ownership_data,
):
    medium_id = ownership_data["medium_b_id"]

    response = client.delete(
        f"/medium/delete-medium/{medium_id}",
        headers=auth_header(
            ownership_data["user_a_id"]
        ),
    )

    assert response.status_code == 404

    medium = db.session.get(
        Medium,
        medium_id,
    )

    assert medium is not None
    
def test_user_can_delete_own_medium(
    client,
    auth_header,
    ownership_data,
):
    medium_id = ownership_data["medium_a_id"]

    response = client.delete(
        f"/medium/delete-medium/{medium_id}",
        headers=auth_header(
            ownership_data["user_a_id"]
        ),
    )

    assert response.status_code == 200

    db.session.expire_all()

    medium = db.session.get(
        Medium,
        medium_id,
    )

    assert medium is None
    
def test_user_cannot_bulk_delete_foreign_media(
    client,
    auth_header,
    ownership_data,
):
    foreign_medium_id = ownership_data["medium_b_id"]

    response = client.delete(
        "/medium/delete-media",
        json=[foreign_medium_id],
        headers=auth_header(
            ownership_data["user_a_id"]
        ),
    )

    assert response.status_code == 404

    medium = db.session.get(
        Medium,
        foreign_medium_id,
    )

    assert medium is not None