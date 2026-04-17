"""Borg REST API routes.

Online serving surface. All endpoints are latency-sensitive.
The background worker handles offline extraction separately.

Every endpoint has OpenAPI metadata: tags, summary, description,
response_model, and status codes for Swagger docs.
"""

import json as json_lib
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Security

from borg.auth import (
    Principal,
    require_admin_access,
    require_namespace_access,
    require_read_access,
    require_write_access,
)
from borg.compiler import compile_context
from borg.config import settings
from borg.ingestion import ingest_episode
from borg.models import (
    ConflictListResponse,
    EntityListResponse,
    EpisodeCreate,
    EpisodeDetailResponse,
    EpisodeResponse,
    FactListResponse,
    NamespaceConfigCreate,
    NamespaceConfigUpdate,
    NamespaceDetailResponse,
    NamespaceListResponse,
    PredicateListResponse,
    ProcedureListResponse,
    QueueResponse,
    RecallRequest,
    RecallResponse,
    RecallResult,
    SnapshotResponse,
    SnapshotTriggerResponse,
    ThinkRequest,
    ThinkResponse,
)
from borg.namespaces import NamespaceStr
from borg.rate_limit import enforce_principal_rate_limit

router = APIRouter(prefix="/api")


def _safe_json(value) -> dict | list:
    """Safely parse a JSONB column that may come back as str, dict, list, or None."""
    if value is None:
        return {}
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json_lib.loads(value)
        except (json_lib.JSONDecodeError, TypeError):
            return {}
    return {}


def _fact_review_state(value) -> tuple[bool, list[str]]:
    properties = _safe_json(value)
    review_required = bool(properties.get("review_required", False))
    review_reasons = properties.get("review_reasons", [])
    if not isinstance(review_reasons, list):
        review_reasons = []
    return review_required, [str(reason) for reason in review_reasons]


async def require_read_access_limited(
    principal: Principal = Security(require_read_access),
) -> Principal:
    enforce_principal_rate_limit("think", principal, settings.borg_rate_limit_think_per_minute)
    return principal


async def require_write_access_limited(
    principal: Principal = Security(require_write_access),
) -> Principal:
    enforce_principal_rate_limit("learn", principal, settings.borg_rate_limit_learn_per_minute)
    return principal


async def require_admin_access_limited(
    principal: Principal = Security(require_admin_access),
) -> Principal:
    enforce_principal_rate_limit("admin", principal, settings.borg_rate_limit_admin_per_minute)
    return principal


# ══════════════════════════════════════════════
# Core Endpoints
# ══════════════════════════════════════════════


@router.get(
    "/health",
    tags=["Health"],
    summary="API health check",
)
async def health():
    return {"status": "ok", "service": "borg"}


@router.post(
    "/think",
    response_model=ThinkResponse,
    tags=["Core"],
    summary="Compile context for a query",
    description="""
Run the full online compilation pipeline:

1. **Classify intent** — dual-profile with primary + secondary task class
2. **Retrieve candidates** — vector search, graph traversal, recency, procedures
3. **Rank and trim** — 4-dimension scoring with memory-type weight modifiers
4. **Compile package** — structured XML (Claude/Copilot) or compact JSON (GPT/Codex)
5. **Update access tracking** — increment entity_state and fact_state counters
6. **Audit log** — full trace with score breakdowns and rejection reasons

This is the primary Borg operation. Equivalent to `borg_think` via MCP.
""",
    responses={
        200: {"description": "Compiled context package"},
        401: {"description": "Missing or invalid auth token"},
    },
)
async def api_think(req: ThinkRequest, principal=Security(require_read_access_limited)):
    namespace = await require_namespace_access(
        req.namespace or settings.default_namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    req = req.model_copy(update={"namespace": namespace})
    response, audit = await compile_context(req)
    return response


@router.post(
    "/learn",
    response_model=EpisodeResponse,
    tags=["Core"],
    summary="Ingest an episode",
    description="""
Store a new episode (conversation, decision, note) into Borg.

The episode is persisted immediately with SHA-256 content dedup. Returns in milliseconds.

The background worker then asynchronously:
- Generates a 1536-dim embedding (Azure OpenAI text-embedding-3-small)
- Extracts entities via LLM (up to 10, typed taxonomy)
- Resolves entities (3-pass: exact → alias → semantic 0.92)
- Extracts facts via LLM (up to 8, predicate-validated)
- Checks supersession (same subject+predicate+different object)
- Extracts procedures (up to 3, merged on duplicate)

Check `GET /health` or `GET /api/admin/queue` to monitor processing.
""",
    responses={
        200: {"description": "Episode accepted or duplicate detected"},
        401: {"description": "Missing or invalid auth token"},
    },
)
async def api_learn(ep: EpisodeCreate, principal=Security(require_write_access_limited)):
    await require_namespace_access(
        ep.namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    return await ingest_episode(ep)


@router.post(
    "/recall",
    response_model=RecallResponse,
    tags=["Core"],
    summary="Search memory without compilation",
    description="""
Search raw memory (episodes, facts, procedures) without the compilation pipeline.

Uses vector similarity when embeddings are available, falls back to recency-based
retrieval otherwise. Facts are matched by entity name keyword search.

Returns raw candidates — not compiled, not ranked. For when you want to browse
memory directly rather than get a compiled context package.
""",
    responses={
        200: {"description": "Raw search results"},
        401: {"description": "Missing or invalid auth token"},
    },
)
async def api_recall(req: RecallRequest, principal=Security(require_read_access)):
    namespace = await require_namespace_access(
        req.namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    from borg.db import get_conn

    results = []

    async with get_conn() as conn:
        query_embedding = None
        try:
            from borg.extraction.embed import generate_embedding

            query_embedding = await generate_embedding(req.query)
        except Exception as exc:
            import structlog

            structlog.get_logger().warning(
                "recall.query_embedding_unavailable",
                error_type=type(exc).__name__,
            )

        if req.memory_type in (None, "episodic"):
            if query_embedding:
                rows = await conn.fetch(
                    """SELECT id, content, source, occurred_at,
                              1 - (embedding <=> $1::vector) as similarity
                    FROM borg_episodes
                    WHERE namespace = $2 AND deleted_at IS NULL AND embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector LIMIT $3""",
                    str(query_embedding),
                    namespace,
                    req.limit,
                )
                for row in rows:
                    results.append(
                        RecallResult(
                            id=row["id"],
                            type="episode",
                            content=row["content"][:500],
                            source=row["source"],
                            occurred_at=row["occurred_at"],
                            relevance_score=round(float(row["similarity"]), 4)
                            if row["similarity"]
                            else None,
                        )
                    )
            else:
                rows = await conn.fetch(
                    """SELECT id, content, source, occurred_at FROM borg_episodes
                    WHERE namespace = $1 AND deleted_at IS NULL
                    ORDER BY occurred_at DESC LIMIT $2""",
                    namespace,
                    req.limit,
                )
                for row in rows:
                    results.append(
                        RecallResult(
                            id=row["id"],
                            type="episode",
                            content=row["content"][:500],
                            source=row["source"],
                            occurred_at=row["occurred_at"],
                        )
                    )

        if req.memory_type in (None, "semantic"):
            words = [w for w in req.query.split() if len(w) > 2]
            if words:
                rows = await conn.fetch(
                    """SELECT f.id, f.predicate, f.evidence_status, s.name as subj, o.name as obj
                    FROM borg_facts f
                    JOIN borg_entities s ON f.subject_id = s.id
                    JOIN borg_entities o ON f.object_id = o.id
                    WHERE f.namespace = $1 AND f.valid_until IS NULL AND f.deleted_at IS NULL
                      AND COALESCE((f.properties->>'review_required')::boolean, false) = false
                      AND (LOWER(s.name) LIKE ANY($2) OR LOWER(o.name) LIKE ANY($2))
                    LIMIT $3""",
                    namespace,
                    [f"%{w.lower()}%" for w in words],
                    req.limit,
                )
                for row in rows:
                    results.append(
                        RecallResult(
                            id=row["id"],
                            type="fact",
                            content=f"{row['subj']} {row['predicate']} {row['obj']}",
                            source=row["evidence_status"],
                        )
                    )

        if req.memory_type in (None, "procedural"):
            rows = await conn.fetch(
                """SELECT id, pattern, category, confidence FROM borg_procedures
                WHERE namespace = $1 AND deleted_at IS NULL
                ORDER BY confidence DESC LIMIT $2""",
                namespace,
                req.limit,
            )
            for row in rows:
                results.append(
                    RecallResult(
                        id=row["id"],
                        type="procedure",
                        content=row["pattern"],
                        source=row["category"],
                        relevance_score=row["confidence"],
                    )
                )

    return RecallResponse(results=results, total=len(results), namespace=namespace)


@router.get(
    "/episodes/{episode_id}",
    response_model=EpisodeDetailResponse,
    tags=["Core"],
    summary="Fetch a full episode by ID",
    description="""
Return the complete stored episode content and metadata for a known episode ID.

Use this after `borg_recall` when you want the full body rather than the truncated
preview returned by search results.
""",
    responses={
        200: {"description": "Full stored episode"},
        401: {"description": "Missing or invalid auth token"},
        404: {"description": "Episode not found"},
    },
)
async def api_get_episode(episode_id: UUID, principal=Security(require_read_access)):
    from borg.db import get_conn

    async with get_conn() as conn:
        row = await conn.fetchrow(
            """SELECT id, source, source_id, source_event_id, namespace, content,
                      occurred_at, ingested_at, metadata, participants, processed
               FROM borg_episodes
               WHERE id = $1 AND deleted_at IS NULL""",
            episode_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Episode not found")

    namespace = await require_namespace_access(
        row["namespace"],
        claims=principal.claims,
        permissions=principal.permissions,
    )
    metadata = _safe_json(row["metadata"])

    return EpisodeDetailResponse(
        id=row["id"],
        source=row["source"],
        source_id=row["source_id"],
        source_event_id=row["source_event_id"],
        namespace=namespace,
        content=row["content"],
        occurred_at=row["occurred_at"],
        ingested_at=row["ingested_at"],
        metadata=metadata if isinstance(metadata, dict) else {},
        participants=list(row["participants"] or []),
        processed=bool(row["processed"]),
    )


# ══════════════════════════════════════════════
# Namespace Config CRUD
# ══════════════════════════════════════════════


@router.get(
    "/namespaces",
    response_model=NamespaceListResponse,
    tags=["Namespaces"],
    summary="List all namespaces",
    description="Returns all configured namespaces with their token budgets and descriptions.",
)
async def list_namespaces(_=Security(require_admin_access_limited)):
    from borg.db import get_conn

    async with get_conn() as conn:
        rows = await conn.fetch(
            """SELECT namespace, hot_tier_budget, warm_tier_budget,
                      description, created_at, updated_at
            FROM borg_namespace_config ORDER BY namespace"""
        )
        return {
            "count": len(rows),
            "namespaces": [
                {
                    "namespace": r["namespace"],
                    "hot_tier_budget": r["hot_tier_budget"],
                    "warm_tier_budget": r["warm_tier_budget"],
                    "description": r["description"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                }
                for r in rows
            ],
        }


@router.get(
    "/namespaces/{namespace}",
    response_model=NamespaceDetailResponse,
    tags=["Namespaces"],
    summary="Get namespace details",
    description="Returns config for a specific namespace including entity, fact, episode, and procedure counts.",
    responses={404: {"description": "Namespace not found"}},
)
async def get_namespace(namespace: NamespaceStr, principal=Security(require_admin_access_limited)):
    namespace = await require_namespace_access(
        namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    from borg.db import get_conn

    async with get_conn() as conn:
        config = await conn.fetchrow(
            "SELECT * FROM borg_namespace_config WHERE namespace = $1",
            namespace,
        )
        if not config:
            raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found")

        entity_count = await conn.fetchval(
            "SELECT COUNT(*) FROM borg_entities WHERE namespace = $1 AND deleted_at IS NULL",
            namespace,
        )
        fact_count = await conn.fetchval(
            "SELECT COUNT(*) FROM borg_facts WHERE namespace = $1 AND valid_until IS NULL AND deleted_at IS NULL",
            namespace,
        )
        episode_count = await conn.fetchval(
            "SELECT COUNT(*) FROM borg_episodes WHERE namespace = $1 AND deleted_at IS NULL",
            namespace,
        )
        procedure_count = await conn.fetchval(
            "SELECT COUNT(*) FROM borg_procedures WHERE namespace = $1 AND deleted_at IS NULL",
            namespace,
        )

        return {
            "namespace": config["namespace"],
            "hot_tier_budget": config["hot_tier_budget"],
            "warm_tier_budget": config["warm_tier_budget"],
            "description": config["description"],
            "created_at": config["created_at"].isoformat() if config["created_at"] else None,
            "updated_at": config["updated_at"].isoformat() if config["updated_at"] else None,
            "stats": {
                "entities": entity_count,
                "facts": fact_count,
                "episodes": episode_count,
                "procedures": procedure_count,
            },
        }


@router.post(
    "/namespaces",
    tags=["Namespaces"],
    summary="Create namespace",
    description="Create a new namespace with configurable hot and warm tier token budgets.",
    responses={409: {"description": "Namespace already exists"}},
    status_code=201,
)
async def create_namespace(
    body: NamespaceConfigCreate, principal=Security(require_admin_access_limited)
):
    namespace = await require_namespace_access(
        body.namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    body = body.model_copy(update={"namespace": namespace})
    from borg.db import get_conn

    async with get_conn() as conn:
        existing = await conn.fetchval(
            "SELECT namespace FROM borg_namespace_config WHERE namespace = $1", body.namespace
        )
        if existing:
            raise HTTPException(
                status_code=409, detail=f"Namespace '{body.namespace}' already exists"
            )

        await conn.execute(
            """INSERT INTO borg_namespace_config
            (namespace, hot_tier_budget, warm_tier_budget, description)
            VALUES ($1, $2, $3, $4)""",
            body.namespace,
            body.hot_tier_budget,
            body.warm_tier_budget,
            body.description,
        )
        return {
            "status": "created",
            "namespace": body.namespace,
            "hot_tier_budget": body.hot_tier_budget,
            "warm_tier_budget": body.warm_tier_budget,
        }


@router.put(
    "/namespaces/{namespace}",
    tags=["Namespaces"],
    summary="Update namespace",
    description="Update token budgets or description for an existing namespace. Only provided fields are changed.",
    responses={404: {"description": "Namespace not found"}},
)
async def update_namespace(
    namespace: NamespaceStr,
    body: NamespaceConfigUpdate,
    principal=Security(require_admin_access_limited),
):
    namespace = await require_namespace_access(
        namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    from borg.db import get_conn

    async with get_conn() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM borg_namespace_config WHERE namespace = $1", namespace
        )
        if not existing:
            raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found")

        hot = (
            body.hot_tier_budget
            if body.hot_tier_budget is not None
            else existing["hot_tier_budget"]
        )
        warm = (
            body.warm_tier_budget
            if body.warm_tier_budget is not None
            else existing["warm_tier_budget"]
        )
        desc = body.description if body.description is not None else existing["description"]

        await conn.execute(
            """UPDATE borg_namespace_config
            SET hot_tier_budget = $2, warm_tier_budget = $3, description = $4, updated_at = now()
            WHERE namespace = $1""",
            namespace,
            hot,
            warm,
            desc,
        )
        return {
            "status": "updated",
            "namespace": namespace,
            "hot_tier_budget": hot,
            "warm_tier_budget": warm,
            "description": desc,
        }


@router.delete(
    "/namespaces/{namespace}",
    tags=["Namespaces"],
    summary="Delete namespace config",
    description="Delete a namespace configuration. Does NOT delete entities, facts, or episodes in that namespace. The 'default' namespace cannot be deleted.",
    responses={
        400: {"description": "Cannot delete the default namespace"},
        404: {"description": "Namespace not found"},
    },
)
async def delete_namespace(
    namespace: NamespaceStr, principal=Security(require_admin_access_limited)
):
    namespace = await require_namespace_access(
        namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    if namespace == "default":
        raise HTTPException(status_code=400, detail="Cannot delete the default namespace")

    from borg.db import get_conn

    async with get_conn() as conn:
        result = await conn.execute(
            "DELETE FROM borg_namespace_config WHERE namespace = $1", namespace
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found")
        return {"status": "deleted", "namespace": namespace}


# ══════════════════════════════════════════════
# Admin Endpoints
# ══════════════════════════════════════════════


@router.get(
    "/admin/queue",
    response_model=QueueResponse,
    tags=["Admin"],
    summary="Processing queue status",
    description="Show unprocessed episodes waiting for the background worker, plus count of failed extractions.",
)
async def admin_queue(_=Security(require_admin_access_limited)):
    from borg.db import get_conn

    async with get_conn() as conn:
        unprocessed = await conn.fetch(
            """SELECT id, source, namespace, ingested_at, LENGTH(content) as content_length
            FROM borg_episodes WHERE processed = false AND deleted_at IS NULL
            ORDER BY ingested_at ASC LIMIT 50""",
        )
        failed = await conn.fetchval(
            """SELECT COUNT(*) FROM borg_episodes
            WHERE processed = true AND deleted_at IS NULL AND metadata ? 'extraction_error'""",
        )
        return {
            "queue_depth": len(unprocessed),
            "failed_count": failed,
            "episodes": [
                {
                    "id": str(r["id"]),
                    "source": r["source"],
                    "namespace": r["namespace"],
                    "ingested_at": r["ingested_at"].isoformat() if r["ingested_at"] else None,
                    "content_length": r["content_length"],
                }
                for r in unprocessed
            ],
        }


@router.get(
    "/admin/entities",
    response_model=EntityListResponse,
    tags=["Admin"],
    summary="List entities",
    description="List all entities in a namespace with their serving state (tier, salience score, access count, aliases). Ordered by access count descending.",
)
async def admin_entities(
    namespace: NamespaceStr = Query("default", description="Namespace to list entities from"),
    principal=Security(require_admin_access_limited),
):
    namespace = await require_namespace_access(
        namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    from borg.db import get_conn

    async with get_conn() as conn:
        rows = await conn.fetch(
            """SELECT e.id, e.name, e.entity_type, e.properties,
                      es.tier, es.salience_score, es.access_count, es.last_accessed,
                      array_length(e.source_episodes, 1) as episode_count
            FROM borg_entities e
            LEFT JOIN borg_entity_state es ON es.entity_id = e.id
            WHERE e.namespace = $1 AND e.deleted_at IS NULL
            ORDER BY es.access_count DESC NULLS LAST, e.name""",
            namespace,
        )
        return {
            "namespace": namespace,
            "count": len(rows),
            "entities": [
                {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "type": r["entity_type"],
                    "tier": r["tier"],
                    "salience": r["salience_score"],
                    "access_count": r["access_count"],
                    "last_accessed": r["last_accessed"].isoformat() if r["last_accessed"] else None,
                    "episode_count": r["episode_count"],
                    "aliases": _safe_json(r["properties"]).get("aliases", []),
                }
                for r in rows
            ],
        }


@router.get(
    "/admin/facts",
    response_model=FactListResponse,
    tags=["Admin"],
    summary="List current facts",
    description="List all current (non-superseded, non-deleted) facts in a namespace with salience and access tracking from fact_state.",
)
async def admin_facts(
    namespace: NamespaceStr = Query("default", description="Namespace to list facts from"),
    principal=Security(require_admin_access_limited),
):
    namespace = await require_namespace_access(
        namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    from borg.db import get_conn

    async with get_conn() as conn:
        rows = await conn.fetch(
            """SELECT f.id, f.predicate, f.evidence_status, f.valid_from, f.properties,
                      s.name as subject, o.name as object,
                      fs.salience_score, fs.access_count, fs.last_accessed
            FROM borg_facts f
            JOIN borg_entities s ON f.subject_id = s.id
            JOIN borg_entities o ON f.object_id = o.id
            LEFT JOIN borg_fact_state fs ON fs.fact_id = f.id
            WHERE f.namespace = $1 AND f.valid_until IS NULL AND f.deleted_at IS NULL
            ORDER BY f.created_at DESC""",
            namespace,
        )
        return {
            "namespace": namespace,
            "count": len(rows),
            "facts": [
                {
                    **{
                        "id": str(r["id"]),
                        "subject": r["subject"],
                        "predicate": r["predicate"],
                        "object": r["object"],
                        "status": r["evidence_status"],
                        "valid_from": r["valid_from"].isoformat() if r["valid_from"] else None,
                        "salience": r["salience_score"],
                        "access_count": r["access_count"],
                        "last_accessed": r["last_accessed"].isoformat()
                        if r["last_accessed"]
                        else None,
                    },
                    "review_required": _fact_review_state(r["properties"])[0],
                    "review_reasons": _fact_review_state(r["properties"])[1],
                }
                for r in rows
            ],
        }


@router.get(
    "/admin/procedures",
    response_model=ProcedureListResponse,
    tags=["Admin"],
    summary="List procedures",
    description="List all candidate and promoted procedures in a namespace. Ordered by confidence descending. Procedures with evidence_status='promoted' and confidence >= 0.8 are used in compilation.",
)
async def admin_procedures(
    namespace: NamespaceStr = Query("default", description="Namespace to list procedures from"),
    principal=Security(require_admin_access_limited),
):
    namespace = await require_namespace_access(
        namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    from borg.db import get_conn

    async with get_conn() as conn:
        rows = await conn.fetch(
            """SELECT id, pattern, category, confidence, observation_count,
                      evidence_status, tier, first_observed, last_observed
            FROM borg_procedures
            WHERE namespace = $1 AND deleted_at IS NULL
            ORDER BY confidence DESC, observation_count DESC""",
            namespace,
        )
        return {
            "namespace": namespace,
            "count": len(rows),
            "procedures": [
                {
                    "id": str(r["id"]),
                    "pattern": r["pattern"],
                    "category": r["category"],
                    "confidence": float(r["confidence"]),
                    "observations": r["observation_count"],
                    "status": r["evidence_status"],
                    "tier": r["tier"],
                    "first_observed": r["first_observed"].isoformat()
                    if r["first_observed"]
                    else None,
                    "last_observed": r["last_observed"].isoformat() if r["last_observed"] else None,
                }
                for r in rows
            ],
        }


@router.get(
    "/admin/conflicts",
    response_model=ConflictListResponse,
    tags=["Admin"],
    summary="Entity resolution conflicts",
    description="Show unresolved entity resolution conflicts — cases where the three-pass resolution algorithm found ambiguous matches (top two semantic candidates within 0.03 similarity gap).",
)
async def admin_conflicts(
    namespace: NamespaceStr = Query("default", description="Namespace to check for conflicts"),
    principal=Security(require_admin_access_limited),
):
    namespace = await require_namespace_access(
        namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    from borg.db import get_conn

    async with get_conn() as conn:
        rows = await conn.fetch(
            """SELECT id, entity_name, entity_type, candidates, created_at
            FROM borg_resolution_conflicts WHERE namespace = $1 AND resolved = false
            ORDER BY created_at DESC""",
            namespace,
        )
        return {
            "namespace": namespace,
            "count": len(rows),
            "conflicts": [
                {
                    "id": str(r["id"]),
                    "entity_name": r["entity_name"],
                    "entity_type": r["entity_type"],
                    "candidates": _safe_json(r["candidates"]),
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                for r in rows
            ],
        }


@router.get(
    "/admin/predicates",
    response_model=PredicateListResponse,
    tags=["Admin"],
    summary="Predicate registry",
    description="Show the 24 canonical predicates with usage counts, plus pending non-canonical predicate candidates. Candidates with 5+ occurrences are flagged for promotion review.",
)
async def admin_predicates(_=Security(require_admin_access_limited)):
    from borg.db import get_conn

    async with get_conn() as conn:
        canonical = await conn.fetch(
            "SELECT predicate, category, inverse, usage_count FROM borg_predicates ORDER BY category, predicate"
        )
        candidates = await conn.fetch(
            """SELECT predicate, occurrences FROM borg_predicate_candidates
            WHERE resolved_at IS NULL ORDER BY occurrences DESC"""
        )
        return {
            "canonical": [dict(r) for r in canonical],
            "pending_candidates": [
                {
                    "predicate": r["predicate"],
                    "occurrences": r["occurrences"],
                    "needs_review": r["occurrences"] >= 5,
                }
                for r in candidates
            ],
        }


@router.post(
    "/admin/process-episode",
    tags=["Admin"],
    summary="Manual extraction trigger",
    description="Manually trigger the full extraction pipeline for a specific episode. Runs synchronously and returns extraction metrics (entities, facts, procedures extracted).",
)
async def admin_process_episode(
    episode_id: str = Query(..., description="UUID of the episode to process"),
    _=Security(require_admin_access_limited),
):
    from borg.worker import process_single_episode

    metrics = await process_single_episode(episode_id)
    return {"episode_id": episode_id, "metrics": metrics}


@router.post(
    "/admin/requeue-failed",
    tags=["Admin"],
    summary="Requeue failed episodes",
    description="Requeue episodes that failed extraction (have extraction_error in metadata). Clears the error flag so the background worker picks them up again. Useful after fixing extraction bugs or adding Azure OpenAI credentials.",
)
async def admin_requeue_failed(
    namespace: NamespaceStr | None = Query(
        None, description="Namespace to requeue (omit for all namespaces)"
    ),
    principal=Security(require_admin_access_limited),
):
    if namespace is not None:
        namespace = await require_namespace_access(
            namespace,
            claims=principal.claims,
            permissions=principal.permissions,
        )
    from borg.worker import requeue_failed_episodes

    count = await requeue_failed_episodes(namespace)
    return {"requeued": count, "namespace": namespace or "all"}


@router.post(
    "/admin/snapshot",
    response_model=SnapshotTriggerResponse,
    tags=["Admin"],
    summary="Trigger hot-tier snapshot",
    description="Manually trigger a hot-tier snapshot. Captures current hot entities, facts, and procedures. If namespace is provided, snapshots only that namespace. Otherwise snapshots all configured namespaces.",
)
async def admin_snapshot(
    namespace: NamespaceStr | None = Query(
        None, description="Namespace to snapshot (omit for all)"
    ),
    principal=Security(require_admin_access_limited),
):
    if namespace is not None:
        namespace = await require_namespace_access(
            namespace,
            claims=principal.claims,
            permissions=principal.permissions,
        )
    from borg.worker import trigger_snapshot

    results = await trigger_snapshot(namespace)
    return {"status": "complete", "snapshots": results}


@router.get(
    "/admin/snapshot/latest",
    response_model=SnapshotResponse,
    tags=["Admin"],
    summary="Latest hot-tier snapshot",
    description="Retrieve the most recent hot-tier snapshot for a namespace. Useful for cold-start loading and debugging what was 'hot' at a point in time.",
    responses={404: {"description": "No snapshots found for namespace"}},
)
async def admin_latest_snapshot(
    namespace: NamespaceStr = Query("default", description="Namespace to get snapshot for"),
    principal=Security(require_admin_access_limited),
):
    namespace = await require_namespace_access(
        namespace,
        claims=principal.claims,
        permissions=principal.permissions,
    )
    from borg.snapshots import get_latest_snapshot

    snapshot = await get_latest_snapshot(namespace)
    if not snapshot:
        raise HTTPException(
            status_code=404, detail=f"No snapshots found for namespace '{namespace}'"
        )
    return snapshot


@router.get(
    "/admin/cost-summary",
    tags=["Admin"],
    summary="Extraction cost summary by namespace",
    description="Summarize extraction token usage and estimated cost for a namespace over a lookback period.",
)
async def admin_cost_summary(
    namespace: str = Query(..., description="Namespace to summarize"),
    days: int = Query(30, description="Lookback period in days", ge=1, le=365),
    cost_per_1k_prompt: float = Query(0.00015, description="USD per 1K prompt tokens"),
    cost_per_1k_completion: float = Query(0.0006, description="USD per 1K completion tokens"),
    principal=Security(require_admin_access_limited),
):
    from borg.db import get_conn

    async with get_conn() as conn:
        row = await conn.fetchrow(
            """SELECT
                COALESCE(SUM(prompt_tokens), 0) as total_prompt,
                COALESCE(SUM(completion_tokens), 0) as total_completion,
                COUNT(DISTINCT episode_id) as episode_count
            FROM borg_extraction_costs
            WHERE namespace = $1
              AND created_at >= now() - make_interval(days => $2)""",
            namespace,
            days,
        )
        by_step = await conn.fetch(
            """SELECT extraction_step, SUM(prompt_tokens) as prompt_tokens,
                SUM(completion_tokens) as completion_tokens, COUNT(*) as call_count
            FROM borg_extraction_costs
            WHERE namespace = $1 AND created_at >= now() - make_interval(days => $2)
            GROUP BY extraction_step""",
            namespace,
            days,
        )

    total_prompt = int(row["total_prompt"])
    total_completion = int(row["total_completion"])
    estimated_cost = (
        total_prompt / 1000 * cost_per_1k_prompt + total_completion / 1000 * cost_per_1k_completion
    )

    async with get_conn() as conn:
        avg_tokens = await conn.fetchval(
            """SELECT COALESCE(AVG(compiled_tokens), 0)
            FROM borg_audit_log
            WHERE namespace = $1 AND created_at >= now() - make_interval(days => $2)""",
            namespace,
            days,
        )

    return {
        "namespace": namespace,
        "period_days": days,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "estimated_cost_usd": round(estimated_cost, 4),
        "episode_count": int(row["episode_count"]),
        "avg_context_injection_tokens": round(float(avg_tokens or 0), 1),
        "by_step": {
            r["extraction_step"]: {
                "prompt_tokens": int(r["prompt_tokens"]),
                "completion_tokens": int(r["completion_tokens"]),
                "call_count": int(r["call_count"]),
            }
            for r in by_step
        },
    }
