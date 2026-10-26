"""
Authorization tests.

- Token check (``token_required``): only requests with a valid access token
  reach a protected route; everything else is rejected with 401.
- Ownership on delete endpoints: User A must be able to delete own resources,
  while User B's resources are treated as non-existent (404) and stay
  untouched.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.models import Journey, Medium
from db import db

# Any route protected by ``token_required`` works here. This one needs no test
# data and, without coordinates, calls no external services.
PROTECTED_URL = "/user/get-user-data"


def _token(app, secret=None, algorithm="HS256", **claims):
    """
    Signs a token; by default a valid access token for user 1.

    Pass a claim as ``None`` to leave it out, e.g. ``_token(app, type=None)``.
    """
    payload = {
        "user_id": 1,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        **claims,
    }
    payload = {key: value for key, value in payload.items() if value is not None}
    return jwt.encode(payload, secret or app.config["SECRET_KEY"], algorithm=algorithm)


def _get_protected(client, authorization=None):
    headers = {"Authorization": authorization} if authorization is not None else {}
    return client.get(PROTECTED_URL, headers=headers)


# ---------------------------------------------------------------------------
# Token check (token_required)
# ---------------------------------------------------------------------------


def test_valid_access_token_reaches_route(client, app):
    """A valid access token is accepted and its user id is passed to the route."""
    response = _get_protected(client, f"Bearer {_token(app, user_id=42)}")

    assert response.status_code == 200
    assert response.get_json()["userId"] == 42


def test_bearer_scheme_is_case_insensitive(client, app):
    """``bearer`` is accepted as well as ``Bearer`` (RFC 6750)."""
    response = _get_protected(client, f"bearer {_token(app)}")

    assert response.status_code == 200


def test_missing_authorization_header_is_rejected(client):
    """A request without ``Authorization`` header is rejected."""
    response = _get_protected(client)

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid authorization header"


@pytest.mark.parametrize("authorization", [
    "",                      # empty header
    "Bearer",                # scheme without token
    "some-token",            # token without scheme
    "Basic dXNlcjpwYXNz",    # wrong scheme
    "Bearer token extra",    # too many parts
])
def test_malformed_authorization_header_is_rejected(client, authorization):
    """Headers that are not exactly ``Bearer <token>`` are rejected."""
    response = _get_protected(client, authorization)

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid authorization header"


def test_expired_token_is_rejected(client, app):
    """An expired token is rejected with a dedicated message."""
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)

    response = _get_protected(client, f"Bearer {_token(app, exp=expired)}")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Token has expired"


@pytest.mark.parametrize("token_type", ["refresh", None])
def test_non_access_token_is_rejected(client, app, token_type):
    """Refresh tokens and tokens without ``type`` cannot access routes."""
    response = _get_protected(client, f"Bearer {_token(app, type=token_type)}")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token type"


def test_token_without_user_id_is_rejected(client, app):
    """A correctly signed access token without ``user_id`` is rejected."""
    response = _get_protected(client, f"Bearer {_token(app, user_id=None)}")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token"


def test_token_signed_with_other_secret_is_rejected(client, app):
    """A token signed with a different secret (a forged token) is rejected."""
    token = _token(app, secret="another-secret-that-is-at-least-32-bytes")

    response = _get_protected(client, f"Bearer {token}")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token"


def test_token_with_other_algorithm_is_rejected(client, app):
    """Only HS256 is accepted, even when the token is signed with the right secret."""
    response = _get_protected(client, f"Bearer {_token(app, algorithm='HS512')}")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token"


def test_unsigned_token_is_rejected(client, app):
    """An unsigned token (``alg: none``) must never be accepted."""
    token = jwt.encode({"user_id": 1, "type": "access"}, key=None, algorithm="none")

    response = _get_protected(client, f"Bearer {token}")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token"


def test_tampered_token_is_rejected(client, app):
    """Changing the payload of a signed token invalidates its signature."""
    header, _, signature = _token(app, user_id=1).split(".")
    _, forged_payload, _ = _token(app, user_id=2).split(".")

    response = _get_protected(client, f"Bearer {header}.{forged_payload}.{signature}")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token"


def test_garbage_token_is_rejected(client):
    """A value that is not a JWT at all is rejected."""
    response = _get_protected(client, "Bearer not-a-jwt")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token"


# ---------------------------------------------------------------------------
# Ownership on delete endpoints
# ---------------------------------------------------------------------------


def test_user_cannot_delete_foreign_journey(client, auth_header, ownership_data):
    """Deleting another user's journey returns 404 and keeps the journey."""
    journey_id = ownership_data["journey_b_id"]

    response = client.delete(
        f"/journey/delete-journey/{journey_id}",
        headers=auth_header(ownership_data["user_a_id"]),
    )

    assert response.status_code == 404
    assert db.session.get(Journey, journey_id) is not None


def test_user_can_delete_own_journey(client, auth_header, ownership_data):
    """Deleting an own journey removes it."""
    journey_id = ownership_data["journey_a_id"]

    response = client.delete(
        f"/journey/delete-journey/{journey_id}",
        headers=auth_header(ownership_data["user_a_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Journey, journey_id) is None


def test_user_cannot_delete_foreign_medium(client, auth_header, ownership_data):
    """Deleting another user's medium returns 404 and keeps the medium."""
    medium_id = ownership_data["medium_b_id"]

    response = client.delete(
        f"/medium/delete-medium/{medium_id}",
        headers=auth_header(ownership_data["user_a_id"]),
    )

    assert response.status_code == 404
    assert db.session.get(Medium, medium_id) is not None


def test_user_can_delete_own_medium(client, auth_header, ownership_data):
    """Deleting an own medium removes it."""
    medium_id = ownership_data["medium_a_id"]

    response = client.delete(
        f"/medium/delete-medium/{medium_id}",
        headers=auth_header(ownership_data["user_a_id"]),
    )

    assert response.status_code == 200
    db.session.expire_all()
    assert db.session.get(Medium, medium_id) is None


def test_user_cannot_bulk_delete_foreign_media(client, auth_header, ownership_data):
    """A bulk delete containing a foreign medium is rejected as a whole."""
    medium_id = ownership_data["medium_b_id"]

    response = client.delete(
        "/medium/delete-media",
        json=[medium_id],
        headers=auth_header(ownership_data["user_a_id"]),
    )

    assert response.status_code == 404
    assert db.session.get(Medium, medium_id) is not None
