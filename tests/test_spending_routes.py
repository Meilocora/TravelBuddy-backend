

def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def _spending_payload(name="Taxi"):
    return {
        "name": _field(name),
        "amount": _field(12.5),
        "date": _field("02.09.2026"),
        "category": _field("Transportation"),
    }


def test_create_spending_success(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.spending_routes.SpendingValidation.validate_spending",
        lambda spending: (spending, True),
    )

    response = client.post(
        f"/spending/create-spending/{route_graph_data['minor_stage_id']}",
        json=_spending_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 201


def test_delete_spending_not_found(client, auth_header, route_graph_data):
    response = client.delete(
        "/spending/delete-spending/999999",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 404


def test_get_currencies_success(client, auth_header, route_graph_data):
    response = client.get(
        "/spending/get-currencies",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "currencies" in response.get_json()


def test_update_spending_success(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.spending_routes.SpendingValidation.validate_spending",
        lambda spending: (spending, True),
    )
    monkeypatch.setattr(
        "app.routes.spending_routes.calculate_journey_costs",
        lambda journey_costs: None,
    )

    response = client.post(
        f"/spending/update-spending/{route_graph_data['minor_stage_id']}/{route_graph_data['spending_id']}",
        json=_spending_payload("Updated Taxi"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_delete_spending_success(client, auth_header, route_graph_data):
    response = client.delete(
        f"/spending/delete-spending/{route_graph_data['spending_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_create_spending_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = _spending_payload()
    monkeypatch.setattr(
        "app.routes.spending_routes.SpendingValidation.validate_spending",
        lambda spending: (spending, False),
    )

    response = client.post(
        f"/spending/create-spending/{route_graph_data['minor_stage_id']}",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_update_spending_resource_mismatch(client, auth_header, route_graph_data):
    response = client.post(
        "/spending/update-spending/999999/{}".format(route_graph_data["spending_id"]),
        json=_spending_payload("Mismatch"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 404


def test_create_spending_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.spending_routes.get_user_minor_stage",
        lambda current_user, minorStageId: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/spending/create-spending/{route_graph_data['minor_stage_id']}",
        json=_spending_payload("Err"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_create_spending_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.spending_routes.SpendingValidation.validate_spending",
        lambda spending: (spending, True),
    )
    monkeypatch.setattr(
        "app.routes.spending_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/spending/create-spending/{route_graph_data['minor_stage_id']}",
        json=_spending_payload("Err commit"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_update_spending_commit_exception(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.spending_routes.SpendingValidation.validate_spending",
        lambda spending: (spending, True),
    )
    monkeypatch.setattr(
        "app.routes.spending_routes.db.session.commit",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post(
        f"/spending/update-spending/{route_graph_data['minor_stage_id']}/{route_graph_data['spending_id']}",
        json=_spending_payload("Err update"),
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500


def test_delete_spending_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.spending_routes.db.session.commit",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.delete(
        f"/spending/delete-spending/{route_graph_data['spending_id']}",
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 500
