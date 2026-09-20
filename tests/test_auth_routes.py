import bcrypt
import jwt

from app.models import User
from db import db


def _field(value):
    return {"value": value, "errors": [], "isValid": True}


def test_login_user_success(client, app):
    from app.routes import auth_routes

    auth_routes.SECRET_KEY = app.config["SECRET_KEY"]

    user = User(
        username="login_user",
        email="login@example.com",
        password=bcrypt.hashpw("Secret123!".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
    )
    db.session.add(user)
    db.session.commit()

    payload = {
        "email": _field("login@example.com"),
        "password": _field("Secret123!"),
    }

    response = client.post("/auth/login-user", json=payload)

    assert response.status_code == 200
    body = response.get_json()
    assert "token" in body
    assert "refreshToken" in body


def test_create_user_success(client, app, monkeypatch):
    from app.routes import auth_routes

    auth_routes.SECRET_KEY = app.config["SECRET_KEY"]

    payload = {
        "username": _field("new_user"),
        "email": _field("new_user@example.com"),
        "password": _field("Secret123!"),
        "passwordConfirm": _field("Secret123!"),
    }

    monkeypatch.setattr(
        "app.routes.auth_routes.AuthValidation.validate_signUp",
        lambda signUpData: (signUpData, True),
    )

    response = client.post("/auth/create-user", json=payload)

    assert response.status_code == 201


def test_change_username_success(client, auth_header, route_graph_data, monkeypatch):
    payload = {
        "newUsername": _field("routes_user_renamed")
    }

    monkeypatch.setattr(
        "app.routes.auth_routes.AuthValidation.validate_change_username",
        lambda nameChangeData, currentUserData: (nameChangeData, True),
    )

    response = client.post(
        "/auth/change-username",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert response.get_json()["newUsername"] == "routes_user_renamed"


def test_refresh_token_success(client, app):
    from app.routes import auth_routes

    auth_routes.SECRET_KEY = app.config["SECRET_KEY"]

    user = User(
        username="refresh_user",
        email="refresh@example.com",
        password="hash",
    )
    db.session.add(user)
    db.session.commit()

    token = jwt.encode(
        {
            "user_id": user.id,
            "username": user.username,
            "type": "refresh",
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    response = client.post(
        "/auth/refresh-token",
        json={"refreshToken": token},
    )

    assert response.status_code == 200
    assert "newToken" in response.get_json()


def test_get_user_infos_success(client, auth_header, route_graph_data):
    response = client.get(
        "/auth/get-user-infos",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert "username" in body


def test_change_password_success(client, auth_header, route_graph_data, monkeypatch):
    payload = {
        "oldPassword": _field("OldSecret1!"),
        "newPassword": _field("NewSecret1!"),
        "newPasswordConfirm": _field("NewSecret1!"),
    }

    monkeypatch.setattr(
        "app.routes.auth_routes.AuthValidation.validate_change_password",
        lambda passwordChangeData, currentUserData: (passwordChangeData, True),
    )

    response = client.post(
        "/auth/change-password",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_login_user_invalid_credentials(client):
    payload = {
        "email": _field("missing@example.com"),
        "password": _field("Secret123!"),
    }

    response = client.post("/auth/login-user", json=payload)

    assert response.status_code == 401


def test_create_user_existing_user(client, app, monkeypatch):
    from app.routes import auth_routes

    auth_routes.SECRET_KEY = app.config["SECRET_KEY"]

    user = User(
        username="existing_user",
        email="existing@example.com",
        password="hash",
    )
    db.session.add(user)
    db.session.commit()

    payload = {
        "username": _field("existing_user"),
        "email": _field("existing@example.com"),
        "password": _field("Secret123!"),
        "passwordConfirm": _field("Secret123!"),
    }

    monkeypatch.setattr(
        "app.routes.auth_routes.AuthValidation.validate_signUp",
        lambda signUpData: (signUpData, True),
    )

    response = client.post("/auth/create-user", json=payload)

    assert response.status_code == 400


def test_refresh_token_invalid_type(client, app):
    from app.routes import auth_routes

    auth_routes.SECRET_KEY = app.config["SECRET_KEY"]

    token = jwt.encode(
        {
            "user_id": 1,
            "username": "x",
            "type": "access",
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    response = client.post(
        "/auth/refresh-token",
        json={"refreshToken": token},
    )

    assert response.status_code == 401


def test_refresh_token_user_not_found(client, app):
    from app.routes import auth_routes

    auth_routes.SECRET_KEY = app.config["SECRET_KEY"]

    token = jwt.encode(
        {
            "user_id": 999999,
            "username": "x",
            "type": "refresh",
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    response = client.post(
        "/auth/refresh-token",
        json={"refreshToken": token},
    )

    assert response.status_code == 404


def test_change_username_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = {
        "newUsername": _field("")
    }

    monkeypatch.setattr(
        "app.routes.auth_routes.AuthValidation.validate_change_username",
        lambda nameChangeData, currentUserData: (nameChangeData, False),
    )

    response = client.post(
        "/auth/change-username",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_register_validation_fail(client, monkeypatch):
    payload = {
        "username": _field(""),
        "email": _field("bad"),
        "password": _field("x"),
        "passwordConfirm": _field("y"),
    }

    monkeypatch.setattr(
        "app.routes.auth_routes.AuthValidation.validate_signUp",
        lambda signUpData: (signUpData, False),
    )
    response = client.post("/auth/create-user", json=payload)
    assert response.status_code == 400


def test_refresh_token_exception_branch(client):
    response = client.post(
        "/auth/refresh-token",
        json={"refreshToken": "not-a-jwt"},
    )
    assert response.status_code == 500


def test_change_username_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    monkeypatch.setattr(
        "app.routes.auth_routes.db.get_or_404",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = client.post(
        "/auth/change-username",
        json={"newUsername": _field("x")},
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_change_password_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    payload = {
        "oldPassword": _field("Old"),
        "newPassword": _field("New"),
        "newPasswordConfirm": _field("No"),
    }
    monkeypatch.setattr(
        "app.routes.auth_routes.AuthValidation.validate_change_password",
        lambda passwordChangeData, currentUserData: (passwordChangeData, False),
    )
    response = client.post(
        "/auth/change-password",
        json=payload,
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400


def test_change_password_exception_branch(client, auth_header, route_graph_data, monkeypatch):
    class _BoomQuery:
        def filter_by(self, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.routes.auth_routes.User.query",
        _BoomQuery(),
    )
    response = client.post(
        "/auth/change-password",
        json={"currentPassword": _field("a"), "newPassword": _field("b"), "confirmPassword": _field("b")},
        headers=auth_header(route_graph_data["user_id"]),
    )
    assert response.status_code == 400
