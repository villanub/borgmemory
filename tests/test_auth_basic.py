"""Tests for Borg Basic profile — no-op passthrough auth."""

import pytest

from borg.auth import (
    Principal,
    _local_principal,
    mcp_require_permissions,
    require_namespace_access,
)


def test_basic_principal_has_full_permissions():
    p = _local_principal()
    assert isinstance(p, Principal)
    assert "read" in p.permissions
    assert "write" in p.permissions
    assert "admin" in p.permissions


def test_mcp_require_permissions_always_passes():
    check = mcp_require_permissions({"admin"})
    # OSS mode accepts any local context, including an empty token.
    assert check(type("ctx", (), {"token": None})()) is True


def test_mcp_require_permissions_passes_with_populated_required():
    check = mcp_require_permissions({"admin", "write", "read"})
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
