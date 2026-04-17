"""Borg hot-tier snapshots — periodic snapshot of hot entities, facts, and procedures.

Per spec: "every 24 hours, write a hot-tier snapshot."

Snapshots capture the current hot-tier state for each namespace. This enables:
1. Fast cold-start: load last snapshot instead of recomputing hot tier
2. Drift detection: compare snapshots to see what's changing
3. Debugging: inspect what was "hot" at any point in time

The snapshot writer runs as a periodic task alongside the extraction worker.
"""

import json

import structlog

from borg.db import get_conn

log = structlog.get_logger()


async def write_snapshot(namespace: str) -> dict:
    """Write a hot-tier snapshot for a namespace.

    Captures all entities, facts, and procedures currently in the hot tier.
    Returns summary metrics.
    """
    async with get_conn() as conn:
        # Hot entities: pinned or tier='hot'
        hot_entities = await conn.fetch(
            """SELECT e.id, e.name, e.entity_type,
                      es.salience_score, es.access_count, es.last_accessed
            FROM borg_entities e
            JOIN borg_entity_state es ON es.entity_id = e.id
            WHERE e.namespace = $1
              AND e.deleted_at IS NULL
              AND (es.tier = 'hot' OR es.pinned = true)""",
            namespace,
        )

        # Hot facts: pinned or tier='hot'
        hot_facts = await conn.fetch(
            """SELECT f.id, f.predicate, f.evidence_status,
                      s.name as subject, o.name as object,
                      fs.salience_score, fs.access_count, fs.last_accessed
            FROM borg_facts f
            JOIN borg_entities s ON f.subject_id = s.id
            JOIN borg_entities o ON f.object_id = o.id
            JOIN borg_fact_state fs ON fs.fact_id = f.id
            WHERE f.namespace = $1
              AND f.valid_until IS NULL
              AND f.deleted_at IS NULL
              AND COALESCE((f.properties->>'review_required')::boolean, false) = false
              AND (fs.tier = 'hot' OR fs.pinned = true)""",
            namespace,
        )

        # Hot procedures: promoted + high confidence
        hot_procedures = await conn.fetch(
            """SELECT id, pattern, category, confidence, observation_count
            FROM borg_procedures
            WHERE namespace = $1
              AND deleted_at IS NULL
              AND (tier = 'hot' OR (evidence_status = 'promoted' AND confidence >= 0.8))""",
            namespace,
        )

        # Serialize
        entities_json = [
            {
                "id": str(r["id"]),
                "name": r["name"],
                "type": r["entity_type"],
                "salience": float(r["salience_score"]) if r["salience_score"] else 0,
                "access_count": r["access_count"] or 0,
            }
            for r in hot_entities
        ]

        facts_json = [
            {
                "id": str(r["id"]),
                "triple": f"{r['subject']} {r['predicate']} {r['object']}",
                "status": r["evidence_status"],
                "salience": float(r["salience_score"]) if r["salience_score"] else 0,
                "access_count": r["access_count"] or 0,
            }
            for r in hot_facts
        ]

        procedures_json = [
            {
                "id": str(r["id"]),
                "pattern": r["pattern"],
                "category": r["category"],
                "confidence": float(r["confidence"]) if r["confidence"] else 0,
                "observations": r["observation_count"] or 0,
            }
            for r in hot_procedures
        ]

        # Estimate total tokens (rough: 1 token ≈ 4 chars)
        total_chars = (
            sum(len(json.dumps(e)) for e in entities_json)
            + sum(len(json.dumps(f)) for f in facts_json)
            + sum(len(json.dumps(p)) for p in procedures_json)
        )
        total_tokens = total_chars // 4

        # Write snapshot
        await conn.execute(
            """INSERT INTO borg_snapshots
            (namespace, hot_entities, hot_facts, hot_procedures, total_tokens)
            VALUES ($1, $2, $3, $4, $5)""",
            namespace,
            json.dumps(entities_json),
            json.dumps(facts_json),
            json.dumps(procedures_json),
            total_tokens,
        )

        metrics = {
            "namespace": namespace,
            "hot_entities": len(entities_json),
            "hot_facts": len(facts_json),
            "hot_procedures": len(procedures_json),
            "total_tokens": total_tokens,
        }
        log.info("snapshot.written", **metrics)
        return metrics


async def write_all_snapshots():
    """Write snapshots for all active namespaces.

    Called by the periodic snapshot task.
    """
    async with get_conn() as conn:
        namespaces = await conn.fetch("SELECT namespace FROM borg_namespace_config")

    results = []
    for row in namespaces:
        try:
            metrics = await write_snapshot(row["namespace"])
            results.append(metrics)
        except Exception as e:
            log.error("snapshot.failed", namespace=row["namespace"], error=str(e))
            results.append({"namespace": row["namespace"], "error": str(e)})

    return results


async def get_latest_snapshot(namespace: str) -> dict | None:
    """Retrieve the most recent snapshot for a namespace.

    Useful for cold-start or debugging.
    """
    async with get_conn() as conn:
        row = await conn.fetchrow(
            """SELECT snapshot_at, hot_entities, hot_facts, hot_procedures, total_tokens
            FROM borg_snapshots
            WHERE namespace = $1
            ORDER BY snapshot_at DESC
            LIMIT 1""",
            namespace,
        )
        if not row:
            return None

        return {
            "snapshot_at": row["snapshot_at"].isoformat() if row["snapshot_at"] else None,
            "hot_entities": json.loads(row["hot_entities"]) if row["hot_entities"] else [],
            "hot_facts": json.loads(row["hot_facts"]) if row["hot_facts"] else [],
            "hot_procedures": json.loads(row["hot_procedures"]) if row["hot_procedures"] else [],
            "total_tokens": row["total_tokens"],
        }
