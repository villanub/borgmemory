"""Borg context compiler — the core online pipeline.

Amendment 3: Dual-profile retrieval with merged ranking.
Amendment 4: Namespace-configurable token budgets.
Gap 2+3: Updates entity_state and fact_state access tracking on selection.
"""

import hashlib
import json
import time

import structlog

from borg.compiler.classify import classify_intent
from borg.compiler.format import compile_package
from borg.compiler.rank import rank_and_trim
from borg.compiler.retrieve import retrieve_candidates
from borg.config import settings
from borg.db import get_conn
from borg.models import AuditEntry, ThinkRequest, ThinkResponse

log = structlog.get_logger()


def _audit_query_fingerprint(query: str) -> str:
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
    return f"sha256:{digest};len={len(query)}"


def _audit_score_breakdown(value: object) -> dict:
    if not isinstance(value, dict):
        return {}

    allowed_keys = {
        "relevance",
        "relevance_weighted",
        "recency",
        "stability",
        "provenance",
        "provenance_base",
        "source_affinity",
        "type_weight",
        "composite",
        "excluded",
    }
    return {key: value[key] for key in allowed_keys if key in value}


def _minimize_audit_candidate(candidate: dict) -> dict:
    audit = candidate.get("audit", {}) if isinstance(candidate.get("audit"), dict) else {}
    item = {
        "type": str(candidate.get("type") or audit.get("type") or "unknown"),
        "id": str(candidate.get("id") or audit.get("id") or ""),
    }

    score_breakdown = _audit_score_breakdown(audit.get("score_breakdown"))
    if score_breakdown:
        item["score_breakdown"] = score_breakdown

    rejection_reason = audit.get("rejection_reason")
    if rejection_reason:
        item["rejection_reason"] = str(rejection_reason)

    return item


async def compile_context(req: ThinkRequest) -> tuple[ThinkResponse, AuditEntry]:
    """Run the full online compilation pipeline."""
    ns = req.namespace or settings.default_namespace
    t_start = time.monotonic()

    # Load namespace config (Amendment 4)
    async with get_conn() as conn:
        ns_config = await conn.fetchrow(
            "SELECT hot_tier_budget, warm_tier_budget FROM borg_namespace_config WHERE namespace = $1",
            ns,
        )
    warm_budget = ns_config["warm_tier_budget"] if ns_config else settings.warm_tier_token_budget

    # Stage 1: Intent Classification (Amendment 3: dual-profile)
    t1 = time.monotonic()
    classification = await classify_intent(req.query, req.task_hint)
    t_classify = int((time.monotonic() - t1) * 1000)

    # Stage 2+3: Retrieval — run all profiles, merge candidates
    t2 = time.monotonic()
    all_candidates = []
    seen_ids = set()

    for profile in classification.retrieval_profiles:
        profile_candidates = await retrieve_candidates(
            query=req.query,
            namespace=ns,
            task_class=classification.primary_class,
            retrieval_profile=profile,
        )
        for c in profile_candidates:
            cid = c.get("id", c.get("content", "")[:50])
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_candidates.append(c)

    t_retrieve = int((time.monotonic() - t2) * 1000)

    # Hybrid guarantee: always pull episode candidates as a baseline.
    # The 'writing' and 'chat' profiles omit episode_recall entirely, which
    # leaves the compiled context with no raw episode evidence. Force a pass
    # whenever fewer than 3 episodes are present after the profile loop.
    episode_count = sum(1 for c in all_candidates if c["type"] == "episode")
    if episode_count < 3:
        fallback_eps = await retrieve_candidates(
            query=req.query,
            namespace=ns,
            task_class=classification.primary_class,
            retrieval_profile="episode_recall",
        )
        for c in fallback_eps:
            cid = c.get("id", c.get("content", "")[:50])
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_candidates.append(c)

    # Stage 4: Rank and Trim (Amendment 3: memory weight modifiers)
    t3 = time.monotonic()
    model = req.model or "claude"
    selected, rejected = await rank_and_trim(
        all_candidates,
        req.query,
        warm_budget,
        memory_weights=classification.memory_weights,
        caller_source=model,
    )
    t_rank = int((time.monotonic() - t3) * 1000)

    # Hybrid guarantee: ensure at least 3 episodes survive ranking.
    # Facts can dominate the budget and leave zero episode evidence; this
    # reinstates the highest-scoring rejected episodes if needed.
    min_episodes = 3
    episodes_selected = [s for s in selected if s["type"] == "episode"]
    if len(episodes_selected) < min_episodes:
        needed = min_episodes - len(episodes_selected)
        rejected_eps = sorted(
            [r for r in rejected if r["type"] == "episode"],
            key=lambda r: r.get("scores", {}).get("composite", 0),
            reverse=True,
        )
        for ep in rejected_eps[:needed]:
            ep["audit"]["rejection_reason"] = "hybrid_reinstated"
            selected.append(ep)

    # Stage 5: Compile Package
    t4 = time.monotonic()
    fmt = "structured" if model in ("claude", "copilot") else "compact"
    compiled, token_count = await compile_package(
        selected=selected,
        namespace=ns,
        task_class=classification.primary_class,
        model=model,
        fmt=fmt,
    )
    t_compile = int((time.monotonic() - t4) * 1000)

    total_ms = int((time.monotonic() - t_start) * 1000)

    # ── Gap 2+3: Update access tracking for selected entities and facts ──
    await _update_access_tracking(selected)

    # Build audit entry (Amendment 3: expanded fields)
    audit = AuditEntry(
        task_class=classification.primary_class,
        namespace=ns,
        query_text=_audit_query_fingerprint(req.query),
        target_model=model,
        retrieval_profile=classification.retrieval_profiles[0],
        candidates_found=len(all_candidates),
        candidates_selected=len(selected),
        candidates_rejected=len(rejected),
        selected_items=[_minimize_audit_candidate(s) for s in selected],
        rejected_items=[_minimize_audit_candidate(r) for r in rejected],
        compiled_tokens=token_count,
        output_format=fmt,
        latency_total_ms=total_ms,
        latency_classify_ms=t_classify,
        latency_retrieve_ms=t_retrieve,
        latency_rank_ms=t_rank,
        latency_compile_ms=t_compile,
    )

    # Write audit log (with amendment fields)
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO borg_audit_log
            (task_class, namespace, query_text, target_model, retrieval_profile,
             candidates_found, candidates_selected, candidates_rejected,
             selected_items, rejected_items, compiled_tokens, output_format,
             latency_total_ms, latency_classify_ms, latency_retrieve_ms,
             latency_rank_ms, latency_compile_ms,
             primary_class, secondary_class, primary_confidence,
             secondary_confidence, profiles_executed)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,
                    $18,$19,$20,$21,$22)""",
            classification.primary_class,
            ns,
            audit.query_text,
            model,
            classification.retrieval_profiles[0],
            len(all_candidates),
            len(selected),
            len(rejected),
            json.dumps(audit.selected_items),
            json.dumps(audit.rejected_items),
            token_count,
            fmt,
            total_ms,
            t_classify,
            t_retrieve,
            t_rank,
            t_compile,
            classification.primary_class,
            classification.secondary_class,
            classification.primary_confidence,
            classification.secondary_confidence,
            classification.retrieval_profiles,
        )

    response = ThinkResponse(
        compiled_context=compiled,
        format=fmt,
        tokens=token_count,
        task_class=classification.primary_class,
        namespace=ns,
        candidates_found=len(all_candidates),
        candidates_selected=len(selected),
        latency_ms=total_ms,
    )

    return response, audit


async def _update_access_tracking(selected: list[dict]):
    """Update entity_state and fact_state access counts for selected candidates.

    Runs after compilation so it never blocks the response path on failure.
    Collects all entity/fact IDs from selected candidates and batch-updates.
    """
    entity_ids = set()
    fact_ids = set()

    for c in selected:
        ctype = c.get("type", "")
        cid = c.get("id")
        if not cid:
            continue

        if ctype in ("fact", "graph_fact"):
            fact_ids.add(cid)
            # entity IDs aren't directly in candidates, but we can get them
            # from the fact lookup. We'll update facts directly and let
            # entity access tracking come from graph_neighborhood hits.
        elif ctype == "episode":
            # Episodes don't have entity_state entries, skip
            pass

    # Also collect entity IDs from graph_neighborhood candidates
    # These have from_entity info but not entity UUIDs in the candidate.
    # We'll query by fact_id to get subject_id and object_id.

    if not entity_ids and not fact_ids:
        return

    try:
        async with get_conn() as conn:
            # Update fact_state: access_count + last_accessed
            if fact_ids:
                await conn.execute(
                    """UPDATE borg_fact_state
                    SET access_count = access_count + 1,
                        last_accessed = now(),
                        updated_at = now()
                    WHERE fact_id = ANY($1::uuid[])""",
                    list(fact_ids),
                )

                # Derive entity IDs from the selected facts to update entity_state
                entity_rows = await conn.fetch(
                    """SELECT DISTINCT unnest(ARRAY[subject_id, object_id]) as eid
                    FROM borg_facts
                    WHERE id = ANY($1::uuid[])""",
                    list(fact_ids),
                )
                for row in entity_rows:
                    entity_ids.add(str(row["eid"]))

            # Update entity_state: access_count + last_accessed
            if entity_ids:
                await conn.execute(
                    """UPDATE borg_entity_state
                    SET access_count = access_count + 1,
                        last_accessed = now(),
                        updated_at = now()
                    WHERE entity_id = ANY($1::uuid[])""",
                    list(entity_ids),
                )

    except Exception as e:
        # Never fail the compilation because of access tracking
        log.warning("compiler.access_tracking_failed", error=str(e))
