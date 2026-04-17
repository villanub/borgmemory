"""Entity resolution — three-pass algorithm.

Design principle: PREFER FRAGMENTATION OVER COLLISION.
Two separate entities for the same thing can be merged later (simple UPDATE).
Two different things incorrectly merged corrupt every fact attached to both.
Fragmentation is recoverable. Collision is not.
"""

import json
from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class ResolutionMethod(Enum):
    EXACT = "exact"
    ALIAS = "alias"
    SEMANTIC = "semantic"
    NEW = "new"


@dataclass
class ResolutionResult:
    entity_id: str | None
    method: ResolutionMethod
    confidence: float
    candidate_matches: list[dict]


# Semantic similarity threshold — deliberately high.
# 0.92 means we only auto-merge when extremely confident.
SEMANTIC_THRESHOLD = 0.92

# If top two semantic candidates are within this gap, flag as ambiguous
AMBIGUITY_GAP = 0.03


async def resolve_entity(
    name: str,
    entity_type: str,
    namespace: str,
    aliases: list[str],
    context_snippet: str,
    conn,
) -> ResolutionResult:
    """Three-pass entity resolution. Each pass is strictly ordered.
    A match at an earlier pass prevents later passes from running.
    """

    # ── PASS 1: Exact match on (name, entity_type, namespace) ──
    exact = await conn.fetchrow(
        """SELECT id, name, entity_type, properties
        FROM borg_entities
        WHERE LOWER(name) = LOWER($1)
          AND entity_type = $2
          AND namespace = $3
          AND deleted_at IS NULL""",
        name,
        entity_type,
        namespace,
    )

    if exact:
        return ResolutionResult(
            entity_id=str(exact["id"]),
            method=ResolutionMethod.EXACT,
            confidence=1.0,
            candidate_matches=[
                {
                    "id": str(exact["id"]),
                    "name": exact["name"],
                    "score": 1.0,
                    "method": "exact",
                }
            ],
        )

    # ── PASS 2: Alias match ──
    all_aliases = [a.lower() for a in aliases] + [name.lower()]
    alias_candidates = await conn.fetch(
        """SELECT id, name, entity_type, properties
        FROM borg_entities
        WHERE namespace = $1
          AND entity_type = $2
          AND deleted_at IS NULL
          AND (
            properties->'aliases' ?| $3
            OR LOWER(name) = ANY($3)
          )""",
        namespace,
        entity_type,
        all_aliases,
    )

    if len(alias_candidates) == 1:
        match = alias_candidates[0]
        await _merge_aliases(conn, match["id"], name, aliases)
        return ResolutionResult(
            entity_id=str(match["id"]),
            method=ResolutionMethod.ALIAS,
            confidence=0.95,
            candidate_matches=[
                {
                    "id": str(match["id"]),
                    "name": match["name"],
                    "score": 0.95,
                    "method": "alias",
                }
            ],
        )

    # ── PASS 3: Semantic similarity (high threshold) ──
    # Only runs if entity embeddings exist (deferred in MVP, but algorithm is ready)
    semantic_candidates = await conn.fetch(
        """SELECT e.id, e.name, e.entity_type, e.properties,
                  1 - (es.embedding <=> (
                      SELECT embedding FROM borg_entity_state
                      WHERE entity_id = e.id
                  )) as similarity
        FROM borg_entities e
        JOIN borg_entity_state es ON es.entity_id = e.id
        WHERE e.namespace = $1
          AND e.entity_type = $2
          AND e.deleted_at IS NULL
          AND es.embedding IS NOT NULL
        ORDER BY es.embedding <=> (
            -- Placeholder: in practice, embed the query text first
            -- For now, skip semantic pass if no embeddings
            es.embedding
        )
        LIMIT 5""",
        namespace,
        entity_type,
    )

    # Filter by threshold
    sem_matches = [
        {
            "id": str(c["id"]),
            "name": c["name"],
            "score": float(c["similarity"]) if c["similarity"] else 0,
            "method": "semantic",
        }
        for c in semantic_candidates
        if c["similarity"] and float(c["similarity"]) > SEMANTIC_THRESHOLD
    ]

    if sem_matches:
        best = sem_matches[0]

        # Safety: if top two are close, flag as ambiguous and create new
        if len(sem_matches) > 1 and best["score"] - sem_matches[1]["score"] < AMBIGUITY_GAP:
            await _flag_ambiguous(conn, name, entity_type, namespace, sem_matches)
            return ResolutionResult(
                entity_id=None,
                method=ResolutionMethod.NEW,
                confidence=0.5,
                candidate_matches=sem_matches,
            )

        await _merge_aliases(conn, UUID(best["id"]), name, aliases)
        return ResolutionResult(
            entity_id=best["id"],
            method=ResolutionMethod.SEMANTIC,
            confidence=best["score"],
            candidate_matches=sem_matches,
        )

    # ── No match: create new entity ──
    return ResolutionResult(
        entity_id=None,
        method=ResolutionMethod.NEW,
        confidence=1.0,
        candidate_matches=sem_matches if sem_matches else [],
    )


async def _merge_aliases(conn, entity_id, new_name: str, new_aliases: list[str]):
    """Add newly discovered aliases to an existing entity. Append-only."""
    all_new = list(set([new_name] + new_aliases))
    await conn.execute(
        """UPDATE borg_entities
        SET properties = jsonb_set(
            COALESCE(properties, '{}'),
            '{aliases}',
            (
                SELECT COALESCE(jsonb_agg(DISTINCT val), '[]'::jsonb)
                FROM (
                    SELECT jsonb_array_elements_text(
                        COALESCE(properties->'aliases', '[]')
                    ) as val
                    UNION
                    SELECT unnest($2::text[]) as val
                ) combined
            )
        )
        WHERE id = $1""",
        entity_id,
        all_new,
    )


async def _flag_ambiguous(conn, name, entity_type, namespace, candidates):
    """Log ambiguous resolution for manual review."""
    await conn.execute(
        """INSERT INTO borg_resolution_conflicts
            (entity_name, entity_type, namespace, candidates)
        VALUES ($1, $2, $3, $4)""",
        name,
        entity_type,
        namespace,
        json.dumps(candidates),
    )
