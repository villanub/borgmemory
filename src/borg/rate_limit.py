"""In-process rate limiting for Borg entrypoints.

This is intentionally simple: a per-process sliding window keyed by identity or
client IP. It is enough to add basic abuse controls for local and single-replica
deployments. Multi-replica production setups should still enforce limits at the
ingress layer.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from collections.abc import MutableMapping
from threading import Lock
from time import monotonic

import structlog
from fastapi import HTTPException, status
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from borg.config import settings

log = structlog.get_logger()

_WINDOW_SECONDS = 60


class InMemoryRateLimiter:
    """Sliding-window request limiter keyed by (bucket, identity)."""

    def __init__(self) -> None:
        self._events: MutableMapping[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(
        self,
        bucket: str,
        key: str,
        limit: int,
        window_seconds: int = _WINDOW_SECONDS,
    ) -> None:
        if limit <= 0:
            return

        now = monotonic()
        cutoff = now - window_seconds
        cache_key = (bucket, key)

        with self._lock:
            events = self._events[cache_key]
            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {bucket}. Try again later.",
                )

            events.append(now)


_limiter = InMemoryRateLimiter()


def _client_host(scope: Scope) -> str:
    client = scope.get("client")
    if client and client[0]:
        return str(client[0])
    return "unknown"


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key == name:
            return value.decode("latin-1")
    return None


def _token_fingerprint(authorization: str | None) -> str | None:
    if not authorization:
        return None
    token = authorization.split(" ", 1)[-1].strip()
    if not token:
        return None
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


def principal_rate_limit_key(principal) -> str:
    return str(
        getattr(principal, "object_id", None)
        or getattr(principal, "subject", None)
        or getattr(principal, "name", None)
        or "unknown-principal"
    )


def enforce_principal_rate_limit(bucket: str, principal, limit: int) -> None:
    key = principal_rate_limit_key(principal)
    try:
        _limiter.check(bucket=bucket, key=key, limit=limit)
    except HTTPException:
        log.warning(
            "rate_limit.exceeded",
            bucket=bucket,
            subject=getattr(principal, "subject", None),
            object_id=getattr(principal, "object_id", None),
            limit=limit,
        )
        raise


class MCPTransportSecurityMiddleware:
    """Adds rate limiting and auth-failure logging for the `/mcp` transport."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") != "/mcp":
            await self.app(scope, receive, send)
            return

        authorization = _header(scope, b"authorization")
        transport_key = f"{_client_host(scope)}:{_token_fingerprint(authorization) or 'anonymous'}"

        try:
            _limiter.check(
                bucket="mcp",
                key=transport_key,
                limit=settings.borg_rate_limit_mcp_per_minute,
            )
        except HTTPException as exc:
            response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
            await response(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start" and message.get("status") in {401, 403}:
                log.warning(
                    "auth.failed",
                    surface="mcp",
                    path=scope.get("path"),
                    client_host=_client_host(scope),
                    has_authorization=bool(authorization),
                    status_code=message["status"],
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)
