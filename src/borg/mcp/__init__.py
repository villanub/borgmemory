"""Borg MCP Server — using FastMCP 3.x.

Exposes four tools via the Streamable HTTP transport:
  - borg_think: compile context (online pipeline)
  - borg_learn: ingest episode (queued for offline processing)
  - borg_recall: raw search across memory types
  - borg_get_episode: fetch a full stored episode by ID
"""

import json
from uuid import UUID

from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

from borg.auth import (
    build_fastmcp_auth_provider,
    mcp_require_permissions,
    require_namespace_access,
)
from borg.namespaces import normalize_namespace

MCP_PATH = "/mcp"

mcp_server = FastMCP(
    "borg",
    auth=build_fastmcp_auth_provider(),
)

mcp_http_app = mcp_server.http_app(
    path=MCP_PATH,
    transport="streamable-http",
    json_response=True,
    stateless_http=True,
)


@mcp_server.tool(
    name="borg_think",
    description="Compile professional context for a query. Call before complex tasks to get relevant knowledge, past decisions, and work patterns.",
    auth=mcp_require_permissions(),
)
async def borg_think(
    query: str,
    namespace: str = "default",
    model: str = "claude",
    task_hint: str | None = None,
    token: AccessToken | None = CurrentAccessToken(),
) -> str:
    """Compile task-specific context from the knowledge graph."""
    from borg.compiler import compile_context
    from borg.models import ThinkRequest

    claims = token.claims if token else {}
    namespace = await require_namespace_access(
        namespace,
        claims=claims,
        permissions=frozenset(),
    )
    req = ThinkRequest(
        query=query,
        namespace=namespace,
        model=model,
        task_hint=task_hint,
    )
    response, _ = await compile_context(req)
    return response.compiled_context


@mcp_server.tool(
    name="borg_learn",
    description="Record a significant decision, discovery, or conversation for future reference. Processing happens in the background.",
    auth=mcp_require_permissions(),
)
async def borg_learn(
    content: str,
    source: str,
    namespace: str,
    metadata: dict | None = None,
    token: AccessToken | None = CurrentAccessToken(),
) -> str:
    """Ingest a new episode into the knowledge graph."""
    from borg.ingestion import ingest_episode
    from borg.models import EpisodeCreate

    claims = token.claims if token else {}
    namespace = await require_namespace_access(
        namespace,
        claims=claims,
        permissions=frozenset(),
    )
    ep = EpisodeCreate(
        content=content,
        source=source,
        namespace=namespace,
        metadata=metadata or {},
    )
    result = await ingest_episode(ep)
    msg = f"Episode {result.status}: {result.episode_id}"
    if result.status == "accepted":
        msg += " (queued for background extraction)"
    return msg


@mcp_server.tool(
    name="borg_recall",
    description="Search memory directly without compilation. Returns raw episodes, facts, and procedures matching your query.",
    auth=mcp_require_permissions(),
)
async def borg_recall(
    query: str,
    namespace: str,
    memory_type: str | None = None,
    token: AccessToken | None = CurrentAccessToken(),
) -> str:
    """Search memory with vector similarity when available."""
    from borg.db import get_conn

    claims = token.claims if token else {}
    namespace = await require_namespace_access(
        normalize_namespace(namespace),
        claims=claims,
        permissions=frozenset(),
    )
    parts = []

    async with get_conn() as conn:
        if memory_type in (None, "episodic"):
            try:
                from borg.extraction.embed import generate_embedding

                emb = await generate_embedding(query)
                rows = await conn.fetch(
                    """SELECT id, source, content, occurred_at,
                              1 - (embedding <=> $1::vector) as similarity
                    FROM borg_episodes
                    WHERE namespace = $2 AND deleted_at IS NULL AND embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector LIMIT 5""",
                    str(emb),
                    namespace,
                )
            except Exception:
                rows = await conn.fetch(
                    """SELECT id, source, content, occurred_at, NULL as similarity
                    FROM borg_episodes
                    WHERE namespace = $1 AND deleted_at IS NULL
                    ORDER BY occurred_at DESC LIMIT 5""",
                    namespace,
                )

            if rows:
                parts.append("## Episodes")
                for r in rows:
                    dt = r["occurred_at"].strftime("%Y-%m-%d") if r["occurred_at"] else "?"
                    sim = f" (sim:{r['similarity']:.3f})" if r["similarity"] else ""
                    parts.append(f"- [{r['source']} {dt}]{sim} {r['content'][:200]}")

        if memory_type in (None, "semantic"):
            words = [w for w in query.split() if len(w) > 2]
            if words:
                rows = await conn.fetch(
                    """SELECT s.name as subj, f.predicate, o.name as obj, f.evidence_status
                    FROM borg_facts f
                    JOIN borg_entities s ON f.subject_id = s.id
                    JOIN borg_entities o ON f.object_id = o.id
                    WHERE f.namespace = $1 AND f.valid_until IS NULL AND f.deleted_at IS NULL
                      AND COALESCE((f.properties->>'review_required')::boolean, false) = false
                      AND (LOWER(s.name) LIKE ANY($2) OR LOWER(o.name) LIKE ANY($2))
                    LIMIT 10""",
                    namespace,
                    [f"%{w.lower()}%" for w in words],
                )
                if rows:
                    parts.append("## Facts")
                    for r in rows:
                        parts.append(
                            f"- {r['subj']} {r['predicate']} {r['obj']} [{r['evidence_status']}]"
                        )

        if memory_type in (None, "procedural"):
            rows = await conn.fetch(
                """SELECT pattern, confidence, observation_count
                FROM borg_procedures
                WHERE namespace = $1 AND deleted_at IS NULL AND evidence_status = 'promoted'
                ORDER BY confidence DESC LIMIT 5""",
                namespace,
            )
            if rows:
                parts.append("## Procedures")
                for r in rows:
                    parts.append(
                        f"- [{r['confidence']:.2f}] {r['pattern']} (seen {r['observation_count']}x)"
                    )

    return "\n".join(parts) if parts else "No memories found in this namespace."


@mcp_server.tool(
    name="borg_get_episode",
    description="Fetch a full stored episode by ID after using borg_recall to find the matching preview.",
    auth=mcp_require_permissions(),
)
async def borg_get_episode(
    episode_id: str,
    token: AccessToken | None = CurrentAccessToken(),
) -> str:
    """Return the full stored content for a single episode."""
    from borg.db import get_conn

    try:
        episode_uuid = UUID(episode_id)
    except ValueError:
        return "Episode not found."

    async with get_conn() as conn:
        row = await conn.fetchrow(
            """SELECT id, source, source_id, source_event_id, namespace, content,
                      occurred_at, ingested_at, metadata, participants, processed
               FROM borg_episodes
               WHERE id = $1 AND deleted_at IS NULL""",
            episode_uuid,
        )

    if not row:
        return "Episode not found."

    claims = token.claims if token else {}
    namespace = await require_namespace_access(
        row["namespace"],
        claims=claims,
        permissions=frozenset(),
    )
    occurred_at = row["occurred_at"].isoformat() if row["occurred_at"] else "?"
    ingested_at = row["ingested_at"].isoformat() if row["ingested_at"] else "?"
    participants = ", ".join(row["participants"] or []) or "-"
    metadata = row["metadata"]
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}
    elif metadata is None:
        metadata = {}

    return "\n".join(
        [
            "## Episode",
            f"- id: {row['id']}",
            f"- namespace: {namespace}",
            f"- source: {row['source']}",
            f"- source_id: {row['source_id'] or '-'}",
            f"- source_event_id: {row['source_event_id'] or '-'}",
            f"- occurred_at: {occurred_at}",
            f"- ingested_at: {ingested_at}",
            f"- processed: {str(bool(row['processed'])).lower()}",
            f"- participants: {participants}",
            f"- metadata: {json.dumps(metadata, sort_keys=True)}",
            "",
            "### Content",
            row["content"],
        ]
    )
