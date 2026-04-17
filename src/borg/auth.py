"""Authentication passthrough for OSS Borg — single-user, local, no auth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Header
from starlette.types import ASGIApp, Receive, Scope, Send

from borg.namespaces import normalize_namespace


@dataclass(frozen=True)
class Principal:
    subject: str
    object_id: str | None
    name: str | None
    permissions: frozenset[str]
    claims: dict[str, Any]


def _local_principal() -> Principal:
    return Principal(
        subject="local",
        object_id=None,
        name="local-user",
        permissions=frozenset({"read", "write", "admin"}),
        claims={},
    )


async def require_namespace_access(namespace: str, **_: Any) -> str:
    return normalize_namespace(namespace)


def require_permissions(_required: set[str] | None = None):
    async def dependency(
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> Principal:
        return _local_principal()

    return dependency


async def require_authenticated() -> Principal:
    return _local_principal()


async def require_read_access() -> Principal:
    return _local_principal()


async def require_write_access() -> Principal:
    return _local_principal()


async def require_admin_access() -> Principal:
    return _local_principal()


def build_fastmcp_auth_provider():
    return None


def mcp_require_permissions(_required: set[str] | None = None):
    return lambda _ctx: True


class EntraBearerAuthMiddleware:
    """Compatibility middleware — OSS has no auth; this passes through unchanged."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            scope["borg_principal"] = _local_principal()
        await self.app(scope, receive, send)
