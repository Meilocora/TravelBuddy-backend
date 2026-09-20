from datetime import datetime

from app.models import Transportation
from db import db



def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _transport_payload():
    return {
        "type": _field("Train"),
        "start_time": _field("01.09.2026 10:00"),
        "arrival_time": _field("01.09.2026 12:00"),
        "place_of_departure": _field("A"),
        "departure_latitude": _field(None),
        "departure_longitude": _field(None),
        "place_of_arrival": _field("B"),
        "arrival_latitude": _field(None),
        "arrival_longitude": _field(None),
        "transportation_costs": _field(50),
        "link": _field(""),
    }


def test_create_major_stage_transportation_success(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, True),
    )

    response = client.post(
        f"/transportation/create-major-stage-transportation/{route_graph_data['major_stage_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_update_minor_stage_transportation_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.post(
        f"/transportation/update-minor-stage-transportation/{route_graph_data['minor_stage_id']}/999999",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_major_stage_transportation_success(
    client,
    auth_header,
    route_graph_data,
):
    response = client.delete(
        f"/transportation/delete-major-stage-transportation/{route_graph_data['major_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_minor_stage_transportation_success(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, True),
    )

    response = client.post(
        f"/transportation/create-minor-stage-transportation/{route_graph_data['minor_stage_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_update_major_stage_transportation_success(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, True),
    )

    response = client.post(
        f"/transportation/update-major-stage-transportation/{route_graph_data['major_stage_id']}/{route_graph_data['transportation_major_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_delete_minor_stage_transportation_success(
    client,
    auth_header,
    route_graph_data,
):
    response = client.delete(
        f"/transportation/delete-minor-stage-transportation/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_major_stage_transportation_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.post(
        "/transportation/create-major-stage-transportation/999999",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_create_minor_stage_transportation_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.post(
        "/transportation/create-minor-stage-transportation/999999",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_major_stage_transportation_validation_fail(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, False),
    )

    response = client.post(
        f"/transportation/update-major-stage-transportation/{route_graph_data['major_stage_id']}/{route_graph_data['transportation_major_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_delete_major_stage_transportation_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.delete(
        "/transportation/delete-major-stage-transportation/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_update_minor_stage_transportation_success(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    minor_transport = Transportation(
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
    db.session.add(minor_transport)
    db.session.commit()

    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, True),
    )

    response = client.post(
        f"/transportation/update-minor-stage-transportation/{route_graph_data['minor_stage_id']}/{minor_transport.id}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_update_minor_stage_transportation_validation_fail(
    client,
    auth_header,
    route_graph_data,
    monkeypatch,
):
    minor_transport = Transportation(
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
    db.session.add(minor_transport)
    db.session.commit()

    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, False),
    )

    response = client.post(
        f"/transportation/update-minor-stage-transportation/{route_graph_data['minor_stage_id']}/{minor_transport.id}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_update_major_stage_transportation_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.post(
        "/transportation/update-major-stage-transportation/999999/999999",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_delete_minor_stage_transportation_not_found(
    client,
    auth_header,
    route_graph_data,
):
    response = client.delete(
        "/transportation/delete-minor-stage-transportation/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_create_major_transportation_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, False),
    )
    response = client.post(
        f"/transportation/create-major-stage-transportation/{route_graph_data['major_stage_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_create_minor_transportation_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, False),
    )
    response = client.post(
        f"/transportation/create-minor-stage-transportation/{route_graph_data['minor_stage_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_update_major_transportation_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, True),
    )
    monkeypatch.setattr(
        "app.routes.transportation_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/transportation/update-major-stage-transportation/{route_graph_data['major_stage_id']}/{route_graph_data['transportation_major_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_update_minor_transportation_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    minor_transport = Transportation(
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
    db.session.add(minor_transport)
    db.session.commit()
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, True),
    )
    monkeypatch.setattr(
        "app.routes.transportation_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        f"/transportation/update-minor-stage-transportation/{route_graph_data['minor_stage_id']}/{minor_transport.id}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_create_major_transportation_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, True),
    )
    monkeypatch.setattr(
        "app.routes.transportation_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/transportation/create-major-stage-transportation/{route_graph_data['major_stage_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_create_minor_transportation_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.transportation_routes.TransportationValidation.validate_transportation",
        lambda transportation: (transportation, True),
    )
    monkeypatch.setattr(
        "app.routes.transportation_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/transportation/create-minor-stage-transportation/{route_graph_data['minor_stage_id']}",
        json=_transport_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_delete_major_transportation_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.transportation_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.delete(
        f"/transportation/delete-major-stage-transportation/{route_graph_data['major_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500


def test_delete_minor_transportation_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.transportation_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.delete(
        f"/transportation/delete-minor-stage-transportation/{route_graph_data['minor_stage_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 500
