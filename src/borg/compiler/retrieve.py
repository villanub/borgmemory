"""Stage 2+3: Candidate retrieval — 4 strategies, namespace-scoped.

Amendment 3: Each strategy is called independently. The compiler
runs multiple profiles and merges results before ranking.

Vector search is used when episode embeddings are available.
Falls back to recency-based retrieval otherwise.
"""

import structlog

from borg.config import settings
from borg.db import get_conn

log = structlog.get_logger()


async def retrieve_candidates(
    query: str,
    namespace: str,
    task_class: str,
    retrieval_profile: str,
) -> list[dict]:
    """Run a single retrieval profile. Returns candidates for merging."""

    if retrieval_profile == "fact_lookup":
        return await _fact_lookup(query, namespace)
    elif retrieval_profile == "episode_recall":
        return await _episode_recall(query, namespace)
    elif retrieval_profile == "graph_neighborhood":
        return await _graph_neighborhood(query, namespace)
    elif retrieval_profile == "procedure_assist":
        return await _procedure_assist(namespace)
    else:
        return []


async def _get_query_embedding(query: str) -> list[float] | None:
    """Generate embedding for a query. Returns None if embedding service is unavailable."""
    try:
        from borg.extraction.embed import generate_embedding

        return await generate_embedding(query)
    except Exception as e:
        log.warning("retrieval.embedding_unavailable", error=str(e))
        return None


async def _fact_lookup(query: str, namespace: str) -> list[dict]:
    """Retrieve current facts by entity name matching."""
    async with get_conn() as conn:
        # Keep words >= 3 chars to filter stopwords, but also include 2-char
        # all-uppercase tokens so abbreviations like IP, VM, DB, SB match entities.
        words = [w for w in query.split() if len(w) >= 3 or (len(w) == 2 and w.isupper())]
        if not words:
            return []

        rows = await conn.fetch(
            """
            SELECT f.id, f.predicate, f.evidence_status, f.valid_from, f.properties,
                   s.name as subject_name, s.entity_type as subject_type,
                   o.name as object_name, o.entity_type as object_type
            FROM borg_facts f
            JOIN borg_entities s ON f.subject_id = s.id
            JOIN borg_entities o ON f.object_id = o.id
            WHERE f.namespace = $1
              AND f.valid_until IS NULL
              AND f.deleted_at IS NULL
              AND COALESCE((f.properties->>'review_required')::boolean, false) = false
              AND (LOWER(s.name) LIKE ANY($2) OR LOWER(o.name) LIKE ANY($2))
            LIMIT $3
            """,
            namespace,
            [f"%{w.lower()}%" for w in words],
            settings.max_candidates,
        )

        return [
            {
                "type": "fact",
                "id": str(row["id"]),
                "content": f"{row['subject_name']} {row['predicate']} {row['object_name']}",
                "evidence_status": row["evidence_status"],
                "valid_from": row["valid_from"].isoformat() if row["valid_from"] else None,
                "source": "fact_lookup",
                "audit": {
                    "type": "fact",
                    "id": str(row["id"]),
                    "predicate": row["predicate"],
                    "status": row["evidence_status"],
                },
            }
            for row in rows
        ]


def _build_episode_content(row: dict, max_chars: int = 1200) -> str:
    """Build episode content string, appending extracted specific_facts if present.

    Truncates base content to max_chars, then appends any specific_facts stored
    in metadata (extracted during ingestion) as a compact suffix. This ensures
    named resources, counts, IPs, and CLI commands survive even long episode truncation.
    """
    content = row["content"][:max_chars]
    metadata = row.get("metadata") or {}
    if isinstance(metadata, str):
        import json as _json

        try:
            metadata = _json.loads(metadata)
        except Exception:
            metadata = {}
    specific_facts = metadata.get("specific_facts", [])
    if specific_facts and isinstance(specific_facts, list):
        facts_str = "; ".join(str(f) for f in specific_facts[:10])
        content += f"\n[specifics: {facts_str}]"
    return content


async def _episode_recall(query: str, namespace: str) -> list[dict]:
    """Retrieve episodes by vector similarity + recency.

    Uses vector search when embeddings are available.
    Falls back to recency-only otherwise.
    """
    query_embedding = await _get_query_embedding(query)

    async with get_conn() as conn:
        if query_embedding:
            # Vector similarity search — the primary retrieval path
            rows = await conn.fetch(
                """
                SELECT id, source, content, occurred_at, metadata,
                       1 - (embedding <=> $1::vector) as similarity
                FROM borg_episodes
                WHERE namespace = $2
                  AND deleted_at IS NULL
                  AND processed = true
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT 10
                """,
                str(query_embedding),
                namespace,
            )

            return [
                {
                    "type": "episode",
                    "id": str(row["id"]),
                    "content": _build_episode_content(row),
                    "episode_source": row["source"],
                    "source": "episode_recall",
                    "occurred_at": row["occurred_at"].isoformat() if row["occurred_at"] else None,
                    "relevance_score": float(row["similarity"]) if row["similarity"] else None,
                    "audit": {
                        "type": "episode",
                        "id": str(row["id"]),
                        "source": row["source"],
                        "occurred_at": row["occurred_at"].isoformat()
                        if row["occurred_at"]
                        else None,
                        "similarity": round(float(row["similarity"]), 4)
                        if row["similarity"]
                        else None,
                        "retrieval_method": "vector",
                    },
                }
                for row in rows
            ]
        else:
            # Fallback: recency-based retrieval (no embeddings available)
            rows = await conn.fetch(
                """
                SELECT id, source, content, occurred_at, metadata
                FROM borg_episodes
                WHERE namespace = $1
                  AND deleted_at IS NULL
                  AND processed = true
                ORDER BY occurred_at DESC
                LIMIT 10
                """,
                namespace,
            )

            return [
                {
                    "type": "episode",
                    "id": str(row["id"]),
                    "content": _build_episode_content(row),
                    "episode_source": row["source"],
                    "source": "episode_recall",
                    "occurred_at": row["occurred_at"].isoformat() if row["occurred_at"] else None,
                    "audit": {
                        "type": "episode",
                        "id": str(row["id"]),
                        "source": row["source"],
                        "occurred_at": row["occurred_at"].isoformat()
                        if row["occurred_at"]
                        else None,
                        "retrieval_method": "recency_fallback",
                    },
                }
                for row in rows
            ]


async def _graph_neighborhood(query: str, namespace: str) -> list[dict]:
    """1-2 hop traversal from entities mentioned in query."""
    async with get_conn() as conn:
        # Keep words >= 3 chars to filter stopwords, but also include 2-char
        # all-uppercase tokens so abbreviations like IP, VM, DB, SB match entities.
        words = [w for w in query.split() if len(w) >= 3 or (len(w) == 2 and w.isupper())]
        if not words:
            return []

        entities = await conn.fetch(
            """
            SELECT id, name, entity_type
            FROM borg_entities
            WHERE namespace = $1 AND deleted_at IS NULL
              AND LOWER(name) LIKE ANY($2)
            LIMIT 5
            """,
            namespace,
            [f"%{w.lower()}%" for w in words],
        )

        candidates = []
        for entity in entities:
            rows = await conn.fetch(
                "SELECT * FROM borg_traverse($1, $2, $3)",
                entity["id"],
                settings.max_graph_hops,
                namespace,
            )
            allowed_fact_ids = await _visible_graph_fact_ids(
                conn,
                [row["fact_id"] for row in rows if row["fact_id"]],
            )
            for row in rows:
                if row["fact_id"] and row["fact_id"] in allowed_fact_ids:
                    candidates.append(
                        {
                            "type": "graph_fact",
                            "id": str(row["fact_id"]),
                            "content": f"{entity['name']} → {row['predicate']} → {row['entity_name']}",
                            "evidence_status": row["evidence_status"],
                            "hop_depth": row["hop_depth"],
                            "source": "graph_neighborhood",
                            "audit": {
                                "type": "graph_fact",
                                "id": str(row["fact_id"]),
                                "from_entity": entity["name"],
                                "predicate": row["predicate"],
                                "to_entity": row["entity_name"],
                                "hops": row["hop_depth"],
                            },
                        }
                    )

        return candidates


async def _visible_graph_fact_ids(conn, fact_ids: list) -> set:
    if not fact_ids:
        return set()

    rows = await conn.fetch(
        """
        SELECT id
        FROM borg_facts
        WHERE id = ANY($1::uuid[])
          AND deleted_at IS NULL
          AND COALESCE((properties->>'review_required')::boolean, false) = false
        """,
        fact_ids,
    )
    return {row["id"] for row in rows}


async def _procedure_assist(namespace: str) -> list[dict]:
    """Retrieve promoted, high-confidence procedures."""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT id, pattern, category, confidence, observation_count
            FROM borg_procedures
            WHERE namespace = $1
              AND deleted_at IS NULL
              AND evidence_status = 'promoted'
              AND confidence >= 0.8
              AND observation_count >= 3
            ORDER BY confidence DESC
            LIMIT 3
            """,
            namespace,
        )

        return [
            {
                "type": "procedure",
                "id": str(row["id"]),
                "content": row["pattern"],
                "confidence": row["confidence"],
                "source": "procedure_assist",
                "audit": {
                    "type": "procedure",
                    "id": str(row["id"]),
                    "pattern": row["pattern"],
                    "confidence": row["confidence"],
                    "observations": row["observation_count"],
                },
            }
            for row in rows
        ]
