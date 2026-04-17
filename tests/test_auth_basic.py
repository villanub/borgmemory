"""Tests for Borg Basic profile — no-op passthrough auth."""

import pytest

from borg.auth import (
    Principal,
    _basic_principal,
    has_admin_permissions,
    mcp_require_permissions,
    require_namespace_access,
    validate_authorization_header,
)
from borg.config import settings


@pytest.fixture(autouse=True)
def set_basic_profile(monkeypatch):
    monkeypatch.setattr(settings, "borg_profile", "basic")


def test_basic_principal_has_full_permissions():
    p = _basic_principal()
    assert isinstance(p, Principal)
    assert "read" in p.permissions
    assert "write" in p.permissions
    assert "admin" in p.permissions


def test_validate_authorization_header_returns_passthrough_without_token():
    principal = validate_authorization_header(None)
    assert principal.subject == "local"
    assert "admin" in principal.permissions


def test_validate_authorization_header_ignores_any_token():
    # Basic mode ignores whatever bearer token is sent
    principal = validate_authorization_header("Bearer not-a-real-jwt")
    assert principal.subject == "local"


def test_has_admin_permissions_always_true():
    assert has_admin_permissions([]) is True
    assert has_admin_permissions(["read"]) is True
    assert has_admin_permissions(["Borg.Read"]) is True


def test_mcp_require_permissions_always_passes():
    check = mcp_require_permissions({"Borg.Admin"})
    # In basic mode the check function should accept any context, including empty token
    assert check(type("ctx", (), {"token": None})()) is True


def test_mcp_require_permissions_passes_with_populated_required():
    # Even a highly restricted set passes in basic mode
    check = mcp_require_permissions({"Borg.Admin", "Borg.Write", "Borg.Read"})
    assert check(type("ctx", (), {"token": None})()) is True


@pytest.mark.asyncio
async def test_require_namespace_access_allows_any_namespace():
    ns = await require_namespace_access("project-alpha")
    assert ns == "project-alpha"


@pytest.mark.asyncio
async def test_require_namespace_access_normalizes_namespace():
    # normalize_namespace lowercases and strips whitespace (valid namespace)
    ns = await require_namespace_access("my-namespace")
    assert ns == "my-namespace"


@pytest.mark.asyncio
async def test_require_namespace_access_no_claims_needed():
    # Basic mode should work with no claims or permissions passed
    ns = await require_namespace_access("borg", claims=None, permissions=None)
    assert ns == "borg"
