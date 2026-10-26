"""
Unit tests for the ownership-aware lookup helpers in ``resource_access``.

Each ``get_user_*`` helper must return the resource only if it belongs to the
given user, directly or through its parent chain, and ``None`` otherwise.
"""

import pytest

from app.routes.resource_access import (
    get_user_activity,
    get_user_journey,
    get_user_major_stage,
    get_user_medium,
    get_user_minor_stage,
)

LOOKUPS = [
    pytest.param(get_user_journey, "journey", id="journey"),
    pytest.param(get_user_major_stage, "major", id="major_stage"),
    pytest.param(get_user_minor_stage, "minor", id="minor_stage"),
    pytest.param(get_user_activity, "activity", id="activity"),
    pytest.param(get_user_medium, "medium", id="medium"),
]


@pytest.mark.parametrize(("lookup", "resource"), LOOKUPS)
def test_user_can_access_own_resource(ownership_data, lookup, resource):
    """User A can load their own resource."""
    resource_id = ownership_data[f"{resource}_a_id"]

    result = lookup(ownership_data["user_a_id"], resource_id)

    assert result is not None
    assert result.id == resource_id


@pytest.mark.parametrize(("lookup", "resource"), LOOKUPS)
def test_user_cannot_access_foreign_resource(ownership_data, lookup, resource):
    """User A gets ``None`` for the corresponding resource of User B."""
    result = lookup(ownership_data["user_a_id"], ownership_data[f"{resource}_b_id"])

    assert result is None
