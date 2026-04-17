"""Project Borg — FastAPI Application Entry Point.

Runs two concerns:
  1. Online: REST API + MCP server (serves borg_think, borg_learn, borg_recall)
  2. Offline: Background worker (processes episodes → embeddings → entities → facts)

These share a database pool but never block each other.

OpenAPI docs available at /docs (Swagger UI) and /redoc (ReDoc).
MCP endpoint at /mcp (Streamable HTTP transport via FastMCP 3.x).
"""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from borg.api import router as api_router
from borg.config import settings
from borg.db import close_pool, get_pool, run_migrations
from borg.mcp import mcp_http_app
from borg.models import HealthResponse
from borg.rate_limit import MCPTransportSecurityMiddleware
from borg.worker import start_worker, stop_worker

_log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(_log_level),
)
log = structlog.get_logger()

_worker_task: asyncio.Task | None = None

OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Service health, worker status, and queue metrics.",
    },
    {
        "name": "Core",
        "description": (
            "Primary operations: compile context (`borg_think`), ingest episodes (`borg_learn`), "
            "search memory (`borg_recall`)."
        ),
    },
    {
        "name": "Namespaces",
        "description": "CRUD management for namespace configurations and token budgets.",
    },
    {
        "name": "Admin",
        "description": (
            "Inspection and management of the knowledge graph, extraction pipeline, cost tracking, "
            "and processing queue. Includes cost summary, entity/fact/procedure browsing, and "
            "snapshot management."
        ),
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_task

    async with contextlib.AsyncExitStack() as stack:
        # 1. Database pool
        log.info("borg.startup", msg="Initializing database pool")
        await get_pool()

        # 2. Run migrations (idempotent)
        log.info("borg.migrations", msg="Running database migrations")
        await run_migrations()

        # 3. Start the FastMCP sub-app lifecycle
        log.info("borg.mcp", msg="Starting FastMCP HTTP app lifecycle")
        await stack.enter_async_context(mcp_http_app.lifespan(mcp_http_app))

        # 4. Launch background worker
        log.info("borg.worker.launching", msg="Starting offline extraction worker")
        _worker_task = asyncio.create_task(start_worker())

        log.info("borg.ready", msg="Borg engine is online. Your knowledge will be assimilated.")
        yield

    # Shutdown
    log.info("borg.shutdown", msg="Stopping background worker")
    await stop_worker()
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass

    log.info("borg.shutdown", msg="Closing database pool")
    await close_pool()


async def root_health(
    authorization: str | None = Header(
        default=None, alias="Authorization", include_in_schema=False
    ),
):
    from borg.db import get_conn

    try:
        async with get_conn() as conn:
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM borg_episodes WHERE deleted_at IS NULL"
            )
            unprocessed = await conn.fetchval(
                "SELECT COUNT(*) FROM borg_episodes WHERE processed = false AND deleted_at IS NULL"
            )
            entities = await conn.fetchval(
                "SELECT COUNT(*) FROM borg_entities WHERE deleted_at IS NULL"
            )
            facts = await conn.fetchval(
                "SELECT COUNT(*) FROM borg_facts WHERE deleted_at IS NULL AND valid_until IS NULL"
            )
    except Exception:
        total = unprocessed = entities = facts = -1

    return {
        "status": "ok",
        "service": "borg",
        "version": "0.1.0",
        "worker": "running" if _worker_task and not _worker_task.done() else "stopped",
        "queue": {
            "total_episodes": total,
            "unprocessed": unprocessed,
            "entities": entities,
            "current_facts": facts,
        },
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="Project Borg",
        description="""
## PostgreSQL-Native Memory Compiler for AI Workflows

Borg extracts entities, facts, and procedures from your AI conversations into a temporal knowledge graph, then compiles task-specific context for any LLM.

### Pipelines

- **Online** (`borg_think`): classify intent → retrieve candidates → rank → compile → audit
- **Offline** (`borg_learn`): ingest → embed → extract entities → resolve → extract facts → procedures → snapshot

### MCP Integration

The MCP endpoint at `/mcp` uses FastMCP 3.x with the Streamable HTTP transport.

```bash
# Codex CLI (~/.codex/config.toml)
[mcp_servers.borg]
url = "http://localhost:8080/mcp"
```
        """,
        version="0.1.0",
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
        license_info={"name": "Private"},
        contact={"name": "Project Borg"},
        docs_url="/docs" if settings.borg_enable_docs else None,
        redoc_url="/redoc" if settings.borg_enable_docs else None,
        openapi_url="/openapi.json" if settings.borg_enable_docs else None,
    )

    if settings.borg_cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.borg_cors_origins_list,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    if settings.borg_trusted_hosts_list:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.borg_trusted_hosts_list,
        )

    app.include_router(api_router)

    app.add_api_route(
        "/health",
        root_health,
        methods=["GET"],
        response_model=HealthResponse,
        tags=["Health"],
        summary="Service health check",
        description="Returns liveness for unauthenticated callers and detailed worker/queue metrics for authenticated callers.",
    )

    # Mount the FastMCP app LAST at "/".
    # The sub-app serves the /mcp transport endpoint and the OAuth helper routes
    # it needs for discovery and login, including /.well-known/*, /authorize,
    # /token, and /auth/callback.
    app.mount("/", MCPTransportSecurityMiddleware(mcp_http_app))
    return app


app = create_app()
