"""Stage 4: Rank candidates and trim to token budget.

Amendment 3: Applies memory-type weight modifiers per task class.
This biases ranking toward the right memory types without hard-excluding
(except procedural in compliance where weight = 0.0).

Gap 3: Reads fact_state.salience_score into ranking when available.

Source affinity: Episodes from the same tool as the caller get a
provenance boost. Blended into the provenance dimension (70% base + 30%
affinity) to avoid adding a 5th scoring dimension.
"""

from datetime import datetime, timezone


def _recency_score(occurred_at: str | None, max_days: int = 90) -> float:
    """Score 0-1 based on recency. 1.0 = today, decays over max_days."""
    if not occurred_at:
        return 0.3
    try:
        dt = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - dt).days
        return max(0.0, 1.0 - (age_days / max_days))
    except (ValueError, TypeError):
        return 0.3


def _stability_score(candidate: dict) -> float:
    """Score 0-1 based on evidence strength."""
    status = candidate.get("evidence_status", "extracted")
    scores = {
        "user_asserted": 1.0,
        "observed": 0.9,
        "promoted": 0.8,
        "extracted": 0.6,
        "inferred": 0.4,
        "deprecated": 0.1,
        "superseded": 0.0,
    }
    return scores.get(status, 0.5)


def _provenance_score(candidate: dict) -> float:
    """Score 0-1 based on retrieval source quality."""
    source = candidate.get("source", "")
    source_weights = {
        "fact_lookup": 0.8,
        "graph_neighborhood": 0.7,
        "episode_recall": 0.6,
        "procedure_assist": 0.9,
    }
    return source_weights.get(source, 0.5)


# Mapping from ThinkRequest.model to likely episode source values.
# Used for source-affinity boosting: episodes from the same tool as the
# caller are more likely to be contextually relevant.
_MODEL_SOURCE_MAP = {
    "claude": ["claude-code", "claude", "claude-ai"],
    "copilot": ["copilot", "github-copilot"],
    "gpt": ["chatgpt", "gpt", "codex-cli"],
    "local": ["codex-cli", "local"],
}


def _source_affinity(candidate: dict, caller_source: str | None) -> float:
    """Score 0-1 based on whether the episode came from the same tool.

    Returns 1.0 for exact or mapped match, 0.5 for no match or no info.
    Only applies to episode candidates (others return 0.5 — neutral).
    """
    if not caller_source:
        return 0.5
    ep_source = candidate.get("episode_source")
    if not ep_source:
        return 0.5
    # Exact match
    if ep_source == caller_source:
        return 1.0
    # Mapped match (e.g., model="claude" matches episode_source="claude-code")
    mapped = _MODEL_SOURCE_MAP.get(caller_source, [])
    if ep_source in mapped:
        return 1.0
    return 0.5


def _memory_type_of(candidate: dict) -> str:
    """Determine memory type from candidate type."""
    t = candidate.get("type", "")
    if t in ("fact", "graph_fact"):
        return "semantic"
    elif t == "episode":
        return "episodic"
    elif t == "procedure":
        return "procedural"
    return "semantic"


async def rank_and_trim(
    candidates: list[dict],
    query: str,
    token_budget: int,
    memory_weights: tuple[float, float, float] = (1.0, 1.0, 1.0),
    caller_source: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """Rank candidates by 4 dimensions with memory-type weighting, trim to budget.

    memory_weights = (episodic_weight, semantic_weight, procedural_weight)
    caller_source = target model string from ThinkRequest, used for source affinity

    Returns (selected, rejected) where each item includes audit info.
    """
    if not candidates:
        return [], []

    # ── Gap 3: Load salience scores for fact candidates from fact_state ──
    fact_salience = await _load_fact_salience(candidates)

    ep_w, sem_w, proc_w = memory_weights
    weight_map = {
        "episodic": ep_w,
        "semantic": sem_w,
        "procedural": proc_w,
    }

    scored = []
    excluded = []

    for c in candidates:
        mem_type = _memory_type_of(c)
        type_weight = weight_map.get(mem_type, 1.0)

        # Hard exclude if weight is 0.0 (procedural in compliance)
        if type_weight == 0.0:
            c["audit"] = c.get("audit", {})
            c["audit"]["rejection_reason"] = f"{mem_type}_excluded_for_task"
            c["audit"]["score_breakdown"] = {"excluded": True}
            excluded.append(c)
            continue

        # Use vector similarity if available, else placeholder
        relevance = c.get("relevance_score") or 0.7
        recency = _recency_score(c.get("occurred_at"))
        stability = _stability_score(c)
        provenance_base = _provenance_score(c)
        affinity = _source_affinity(c, caller_source)
        # Blend source affinity into provenance: 70% base retrieval quality + 30% tool match
        provenance = provenance_base * 0.7 + affinity * 0.3

        # Gap 3: Blend in fact_state salience if available
        cid = c.get("id")
        if cid and cid in fact_salience:
            salience = fact_salience[cid]
            # Blend salience into stability (salience rewards frequently-accessed,
            # high-value facts without adding a 5th dimension)
            stability = stability * 0.7 + salience * 0.3

        # Apply memory-type weight to relevance dimension
        weighted_relevance = relevance * type_weight

        composite = (
            weighted_relevance * 0.40 + recency * 0.25 + stability * 0.20 + provenance * 0.15
        )

        c["scores"] = {
            "relevance": round(relevance, 3),
            "relevance_weighted": round(weighted_relevance, 3),
            "recency": round(recency, 3),
            "stability": round(stability, 3),
            "provenance": round(provenance, 3),
            "provenance_base": round(provenance_base, 3),
            "source_affinity": round(affinity, 3),
            "memory_type": mem_type,
            "type_weight": round(type_weight, 2),
            "composite": round(composite, 3),
        }
        c["audit"] = c.get("audit", {})
        c["audit"]["score_breakdown"] = c["scores"]
        scored.append(c)

    # Sort by composite score descending
    scored.sort(key=lambda x: x["scores"]["composite"], reverse=True)

    # Deduplicate by content
    seen_content = set()
    deduped = []
    for c in scored:
        content_key = c["content"][:100]
        if content_key not in seen_content:
            seen_content.add(content_key)
            deduped.append(c)

    # Trim to token budget (rough estimate: 1 token ≈ 4 chars)
    selected = []
    rejected = list(excluded)  # start with hard-excluded items
    tokens_used = 0

    for c in deduped:
        est_tokens = len(c["content"]) // 4
        if tokens_used + est_tokens <= token_budget:
            selected.append(c)
            tokens_used += est_tokens
        else:
            c["audit"]["rejection_reason"] = "budget_exceeded"
            rejected.append(c)

    return selected, rejected


async def _load_fact_salience(candidates: list[dict]) -> dict[str, float]:
    """Load salience_score from fact_state for fact/graph_fact candidates.

    Returns {fact_id_str: salience_score} for any facts that have state rows.
    Non-blocking: returns empty dict on failure.
    """
    fact_ids = [
        c["id"] for c in candidates if c.get("type") in ("fact", "graph_fact") and c.get("id")
    ]
    if not fact_ids:
        return {}

    try:
        from borg.db import get_conn

        async with get_conn() as conn:
            rows = await conn.fetch(
                """SELECT fact_id, salience_score
                FROM borg_fact_state
                WHERE fact_id = ANY($1::uuid[])""",
                fact_ids,
            )
            return {str(r["fact_id"]): float(r["salience_score"]) for r in rows}
    except Exception:
        return {}
