"""
Tests for the authentication endpoints (``/auth``).

Covers login, registration, token refresh and account changes. The
``app`` fixture aligns the module-level ``SECRET_KEY`` of ``auth_routes``
with the test configuration, so issued and verified tokens match.
"""

import bcrypt
import jwt
from helpers import field, raise_error, stub_validation

from app.models import User
from db import db

AUTH_VALIDATION = "app.routes.auth_routes.AuthValidation"


def _create_user(username, email, password="hash"):
    """Persists a user; ``password`` is stored as given (hash it if needed)."""
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return user


def _encode_token(app, user_id, token_type):
    """Signs a token with the test secret; ``token_type`` is 'access' or 'refresh'."""
    return jwt.encode(
        {"user_id": user_id, "username": "test-user", "type": token_type},
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )


def _sign_up_payload(username, email):
    return {
        "username": field(username),
        "email": field(email),
        "password": field("Secret123!"),
        "passwordConfirm": field("Secret123!"),
    }


# ---------------------------------------------------------------------------
# POST /auth/login-user
# ---------------------------------------------------------------------------


def test_login_user_success(client):
    """Correct credentials return an access token and a refresh token."""
    hashed_password = bcrypt.hashpw(b"Secret123!", bcrypt.gensalt()).decode("utf-8")
    _create_user("login_user", "login@example.com", hashed_password)

    response = client.post(
        "/auth/login-user",
        json={
            "email": field("login@example.com"),
            "password": field("Secret123!"),
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert "token" in body
    assert "refreshToken" in body


def test_login_user_invalid_credentials(client):
    """Login with an unknown email returns 401."""
    response = client.post(
        "/auth/login-user",
        json={
            "email": field("missing@example.com"),
            "password": field("Secret123!"),
        },
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/create-user
# ---------------------------------------------------------------------------


def test_create_user_success(client, monkeypatch):
    """A valid sign-up creates a new user."""
    monkeypatch.setattr(f"{AUTH_VALIDATION}.validate_signUp", stub_validation(True))

    response = client.post(
        "/auth/create-user",
        json=_sign_up_payload("new_user", "new_user@example.com"),
    )

    assert response.status_code == 201
    created = db.session.execute(
        db.select(User).filter_by(email="new_user@example.com")
    ).scalar_one_or_none()
    assert created is not None


def test_create_user_existing_user(client, monkeypatch):
    """Signing up with an already registered username/email returns 400."""
    _create_user("existing_user", "existing@example.com")
    monkeypatch.setattr(f"{AUTH_VALIDATION}.validate_signUp", stub_validation(True))

    response = client.post(
        "/auth/create-user",
        json=_sign_up_payload("existing_user", "existing@example.com"),
    )

    assert response.status_code == 400


def test_create_user_validation_fail(client, monkeypatch):
    """Invalid sign-up form values are rejected with 400."""
    monkeypatch.setattr(f"{AUTH_VALIDATION}.validate_signUp", stub_validation(False))

    response = client.post(
        "/auth/create-user",
        json={
            "username": field(""),
            "email": field("bad"),
            "password": field("x"),
            "passwordConfirm": field("y"),
        },
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /auth/refresh-token
# ---------------------------------------------------------------------------


def test_refresh_token_success(client, app):
    """A valid refresh token yields a new access token."""
    user = _create_user("refresh_user", "refresh@example.com")

    response = client.post(
        "/auth/refresh-token",
        json={"refreshToken": _encode_token(app, user.id, "refresh")},
    )

    assert response.status_code == 200
    assert "newToken" in response.get_json()


def test_refresh_token_rejects_access_token(client, app):
    """An access token must not be accepted as a refresh token."""
    response = client.post(
        "/auth/refresh-token",
        json={"refreshToken": _encode_token(app, 1, "access")},
    )

    assert response.status_code == 401


def test_refresh_token_user_not_found(client, app):
    """A refresh token for a deleted/unknown user returns 404."""
    response = client.post(
        "/auth/refresh-token",
        json={"refreshToken": _encode_token(app, 999999, "refresh")},
    )

    assert response.status_code == 404


def test_refresh_token_malformed_token_returns_500(client):
    """A token that cannot be decoded is reported as 500 by the current implementation."""
    response = client.post(
        "/auth/refresh-token",
        json={"refreshToken": "not-a-jwt"},
    )

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /auth/get-user-infos
# ---------------------------------------------------------------------------


def test_get_user_infos_success(client, auth_header, route_graph_data):
    """The authenticated user's profile data is returned."""
    response = client.get(
        "/auth/get-user-infos",
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert "username" in response.get_json()


# ---------------------------------------------------------------------------
# POST /auth/change-username
# ---------------------------------------------------------------------------


def test_change_username_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid new username is stored and echoed back."""
    monkeypatch.setattr(f"{AUTH_VALIDATION}.validate_change_username", stub_validation(True))

    response = client.post(
        "/auth/change-username",
        json={"newUsername": field("routes_user_renamed")},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200
    assert response.get_json()["newUsername"] == "routes_user_renamed"


def test_change_username_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """An invalid new username is rejected with 400."""
    monkeypatch.setattr(f"{AUTH_VALIDATION}.validate_change_username", stub_validation(False))

    response = client.post(
        "/auth/change-username",
        json={"newUsername": field("")},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_change_username_lookup_error_returns_400(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected error while loading the user returns 400."""
    monkeypatch.setattr("app.routes.auth_routes.db.get_or_404", raise_error)

    response = client.post(
        "/auth/change-username",
        json={"newUsername": field("x")},
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /auth/change-password
# ---------------------------------------------------------------------------


def _change_password_payload(old="OldSecret1!", new="NewSecret1!", confirm="NewSecret1!"):
    return {
        "oldPassword": field(old),
        "newPassword": field(new),
        "newPasswordConfirm": field(confirm),
    }


def test_change_password_success(client, auth_header, route_graph_data, monkeypatch):
    """A valid password change returns 200."""
    monkeypatch.setattr(f"{AUTH_VALIDATION}.validate_change_password", stub_validation(True))

    response = client.post(
        "/auth/change-password",
        json=_change_password_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 200


def test_change_password_validation_fail(client, auth_header, route_graph_data, monkeypatch):
    """An invalid password change is rejected with 400."""
    monkeypatch.setattr(f"{AUTH_VALIDATION}.validate_change_password", stub_validation(False))

    response = client.post(
        "/auth/change-password",
        json=_change_password_payload(confirm="Mismatch1!"),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400


def test_change_password_lookup_error_returns_400(client, auth_header, route_graph_data, monkeypatch):
    """An unexpected error while loading the user returns 400."""

    class _FailingQuery:
        def filter_by(self, **kwargs):
            raise RuntimeError("Simulated failure")

    monkeypatch.setattr("app.routes.auth_routes.User.query", _FailingQuery())

    response = client.post(
        "/auth/change-password",
        json=_change_password_payload(),
        headers=auth_header(route_graph_data["user_id"]),
    )

    assert response.status_code == 400
