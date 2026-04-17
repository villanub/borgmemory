"""Extraction pipeline — process episodes into entities, facts, and procedures.

Runs in the offline pipeline. Never blocks online queries.

Gracefully degrades if OpenAI is not configured:
- Without credentials: episodes are skipped and marked processed
  with no entities or facts extracted. They're still searchable by recency.
- With credentials: full LLM extraction runs.

Default: standard OpenAI (openai_api_key required).
Optional: Azure OpenAI when AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set.
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime

import structlog

from borg.config import settings
from borg.db import get_conn
from borg.extraction.prompts import (
    CANONICAL_PREDICATES,
    ENTITY_EXTRACTION_PROMPT,
    FACT_EXTRACTION_PROMPT,
    PROCEDURE_EXTRACTION_PROMPT,
    SPECIFIC_FACT_EXTRACTION_PROMPT,
)
from borg.extraction.resolve import ResolutionMethod, resolve_entity

log = structlog.get_logger()

_PROMPT_INJECTION_MARKERS = (
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "developer message",
    "assistant message",
    "follow these instructions",
    "disregard the above",
    "disregard previous",
    "jailbreak",
    "<system>",
    "<assistant>",
    "<developer>",
    "role: system",
    "role: developer",
)
_PROCEDURE_CATEGORIES = {
    "workflow",
    "decision_rule",
    "best_practice",
    "convention",
    "troubleshooting",
}
_PREDICATE_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


@dataclass(frozen=True)
class FactGuardrailDecision:
    action: str
    subject: str
    predicate: str
    object: str
    evidence: str
    valid_from: datetime | None
    custom: bool
    review_reasons: tuple[str, ...] = ()
    reject_reason: str | None = None


@dataclass(frozen=True)
class ProcedureGuardrailDecision:
    action: str
    pattern: str
    category: str
    confidence: float
    reject_reason: str | None = None


def _normalize_whitespace(value: str | None) -> str:
    return " ".join(str(value or "").split())


def _find_prompt_injection_marker(*values: object) -> str | None:
    combined = " ".join(_normalize_whitespace(str(value)) for value in values if value)
    lowered = combined.lower()
    for marker in _PROMPT_INJECTION_MARKERS:
        if marker in lowered:
            return marker
    return None


def _normalize_predicate(value: str | None) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")
    return normalized


def _safe_confidence(value: object) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _evaluate_fact_guardrails(fact: dict, entity_map: dict[str, str]) -> FactGuardrailDecision:
    subject = _normalize_whitespace(fact.get("subject"))
    predicate = _normalize_predicate(fact.get("predicate"))
    object_name = _normalize_whitespace(fact.get("object"))
    evidence = str(fact.get("evidence_strength", "implied")).strip().lower()
    if evidence not in {"explicit", "implied"}:
        evidence = "implied"

    if not all([subject, predicate, object_name]):
        return FactGuardrailDecision(
            action="reject",
            subject=subject,
            predicate=predicate,
            object=object_name,
            evidence=evidence,
            valid_from=None,
            custom=False,
            reject_reason="missing_required_fields",
        )

    if subject == object_name:
        return FactGuardrailDecision(
            action="reject",
            subject=subject,
            predicate=predicate,
            object=object_name,
            evidence=evidence,
            valid_from=None,
            custom=False,
            reject_reason="self_referential_fact",
        )

    if not entity_map.get(subject) or not entity_map.get(object_name):
        return FactGuardrailDecision(
            action="reject",
            subject=subject,
            predicate=predicate,
            object=object_name,
            evidence=evidence,
            valid_from=None,
            custom=False,
            reject_reason="unknown_entity_reference",
        )

    marker = _find_prompt_injection_marker(
        subject,
        fact.get("predicate"),
        object_name,
        json.dumps(fact.get("temporal", {}), sort_keys=True),
    )
    if marker:
        return FactGuardrailDecision(
            action="reject",
            subject=subject,
            predicate=predicate,
            object=object_name,
            evidence=evidence,
            valid_from=None,
            custom=False,
            reject_reason=f"prompt_injection_marker:{marker}",
        )

    if not _PREDICATE_RE.fullmatch(predicate):
        return FactGuardrailDecision(
            action="reject",
            subject=subject,
            predicate=predicate,
            object=object_name,
            evidence=evidence,
            valid_from=None,
            custom=False,
            reject_reason="invalid_predicate_format",
        )

    temporal = fact.get("temporal", {}) if isinstance(fact.get("temporal"), dict) else {}
    raw_valid_from = temporal.get("valid_from")
    valid_from = _parse_temporal_date(raw_valid_from)

    review_reasons: list[str] = []
    is_custom = bool(fact.get("custom", False)) or predicate not in CANONICAL_PREDICATES
    if is_custom:
        review_reasons.append("custom_predicate")
    if evidence == "implied":
        review_reasons.append("implied_evidence")
    if raw_valid_from and valid_from is None:
        review_reasons.append("invalid_temporal_marker")

    return FactGuardrailDecision(
        action="review" if review_reasons else "accept",
        subject=subject,
        predicate=predicate,
        object=object_name,
        evidence=evidence,
        valid_from=valid_from,
        custom=is_custom,
        review_reasons=tuple(review_reasons),
    )


def _evaluate_procedure_guardrails(proc: dict) -> ProcedureGuardrailDecision:
    pattern = _normalize_whitespace(proc.get("pattern"))
    category = _normalize_whitespace(proc.get("category") or "workflow").lower()
    confidence = _safe_confidence(proc.get("confidence", 0.0))

    if not pattern:
        return ProcedureGuardrailDecision(
            action="reject",
            pattern=pattern,
            category=category or "workflow",
            confidence=confidence,
            reject_reason="missing_pattern",
        )

    marker = _find_prompt_injection_marker(pattern)
    if marker:
        return ProcedureGuardrailDecision(
            action="reject",
            pattern=pattern,
            category=category or "workflow",
            confidence=confidence,
            reject_reason=f"prompt_injection_marker:{marker}",
        )

    if len(pattern) < 15:
        return ProcedureGuardrailDecision(
            action="reject",
            pattern=pattern,
            category=category or "workflow",
            confidence=confidence,
            reject_reason="pattern_too_short",
        )

    if len(pattern) > 400:
        return ProcedureGuardrailDecision(
            action="reject",
            pattern=pattern,
            category=category or "workflow",
            confidence=confidence,
            reject_reason="pattern_too_long",
        )

    if category not in _PROCEDURE_CATEGORIES:
        return ProcedureGuardrailDecision(
            action="reject",
            pattern=pattern,
            category=category,
            confidence=confidence,
            reject_reason="invalid_category",
        )

    if confidence < settings.borg_extraction_procedure_min_confidence:
        return ProcedureGuardrailDecision(
            action="reject",
            pattern=pattern,
            category=category,
            confidence=confidence,
            reject_reason="low_confidence",
        )

    return ProcedureGuardrailDecision(
        action="accept",
        pattern=pattern,
        category=category,
        confidence=confidence,
    )


def _parse_temporal_date(value: str | None) -> datetime | None:
    """Try to parse a date string from LLM output into a datetime.

    The LLM may return ISO dates ("2026-03-01"), descriptive strings
    ("session_start", "recently"), or None. Only valid ISO-ish dates
    are returned; everything else becomes None (defaults to now() in SQL).
    """
    if not value or not isinstance(value, str):
        return None

    # Quick reject: if it doesn't start with a digit, it's not a date
    if not value[0].isdigit():
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    # Try fromisoformat as a catch-all
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


async def extract_episode(episode_id: str) -> dict:
    """Run full extraction on a single episode.

    Returns extraction metrics for audit logging.
    """
    metrics = {
        "entities_extracted": 0,
        "entities_resolved": 0,
        "entities_new": 0,
        "facts_extracted": 0,
        "facts_review_required": 0,
        "facts_rejected_guardrail": 0,
        "facts_custom_predicate": 0,
        "evidence_explicit": 0,
        "evidence_implied": 0,
        "procedures_extracted": 0,
        "procedures_merged": 0,
        "procedures_rejected_guardrail": 0,
        "specific_facts_extracted": 0,
        "skipped_no_llm": False,
        "errors": [],
    }

    # Skip if neither standard OpenAI nor Azure OpenAI is configured
    has_openai = bool(settings.openai_api_key)
    has_azure = bool(settings.azure_openai_endpoint and settings.azure_openai_api_key)
    if not has_openai and not has_azure:
        log.info("extraction.skipped", episode_id=episode_id, reason="No LLM provider configured")
        metrics["skipped_no_llm"] = True
        async with get_conn() as conn:
            await conn.execute(
                "UPDATE borg_episodes SET processed = true WHERE id = $1",
                episode_id,
            )
        return metrics

    async with get_conn() as conn:
        episode = await conn.fetchrow(
            "SELECT id, content, namespace FROM borg_episodes WHERE id = $1",
            episode_id,
        )
        if not episode:
            metrics["errors"].append("episode_not_found")
            return metrics

        content = episode["content"]
        namespace = episode["namespace"]

        # Model name for cost tracking
        _cost_model = (
            settings.azure_openai_extraction_deployment
            if settings.azure_openai_endpoint
            else settings.openai_chat_model
        )

        # ── Step 1: Extract entities ──
        try:
            entities = await _call_extraction_llm(
                ENTITY_EXTRACTION_PROMPT % content[:4000],
                label=f"entities/{episode_id[:8]}",
            )
            entity_list = entities.get("entities", [])
            metrics["entities_extracted"] = len(entity_list)
            await _record_extraction_cost(
                namespace,
                episode_id,
                "entities",
                _cost_model,
                entities.get("_prompt_tokens", 0),
                entities.get("_completion_tokens", 0),
            )
        except Exception as e:
            log.error("extraction.entities_failed", episode_id=episode_id, error=str(e))
            metrics["errors"].append(f"entity_extraction: {e}")
            entity_list = []

        # ── Step 2: Resolve entities against existing graph ──
        entity_map = {}
        for ent in entity_list:
            name = ent.get("name", "").strip()
            etype = ent.get("type", "unknown").strip()
            aliases = ent.get("aliases", [])

            if not name:
                continue

            try:
                result = await resolve_entity(
                    name=name,
                    entity_type=etype,
                    namespace=namespace,
                    aliases=aliases,
                    context_snippet=content[:200],
                    conn=conn,
                )

                if result.entity_id:
                    entity_map[name] = result.entity_id
                    if result.method in (
                        ResolutionMethod.EXACT,
                        ResolutionMethod.ALIAS,
                        ResolutionMethod.SEMANTIC,
                    ):
                        metrics["entities_resolved"] += 1
                        await conn.execute(
                            """UPDATE borg_entities
                            SET source_episodes = array_append(
                                COALESCE(source_episodes, '{}'), $2::uuid
                            )
                            WHERE id = $1::uuid
                              AND NOT ($2::uuid = ANY(COALESCE(source_episodes, '{}')))""",
                            result.entity_id,
                            episode_id,
                        )
                else:
                    new_id = await conn.fetchval(
                        """INSERT INTO borg_entities
                        (name, entity_type, namespace, properties, source_episodes)
                        VALUES ($1, $2, $3, $4, ARRAY[$5::uuid])
                        ON CONFLICT (name, entity_type, namespace) DO UPDATE
                          SET source_episodes = array_append(
                              COALESCE(borg_entities.source_episodes, '{}'), $5::uuid
                          )
                        RETURNING id""",
                        name,
                        etype,
                        namespace,
                        json.dumps({"aliases": aliases}),
                        episode_id,
                    )
                    entity_map[name] = str(new_id)
                    metrics["entities_new"] += 1

                    await conn.execute(
                        """INSERT INTO borg_entity_state (entity_id)
                        VALUES ($1) ON CONFLICT DO NOTHING""",
                        new_id,
                    )
            except Exception as e:
                log.error("extraction.entity_resolve_failed", name=name, error=str(e))
                metrics["errors"].append(f"entity_resolve({name}): {e}")

        # ── Step 3: Extract facts ──
        if entity_map:
            entity_names = list(entity_map.keys())
            predicate_list = "\n".join(f"- {p}" for p in CANONICAL_PREDICATES)

            try:
                facts = await _call_extraction_llm(
                    FACT_EXTRACTION_PROMPT
                    % (
                        ", ".join(entity_names),
                        predicate_list,
                        content[:4000],
                    ),
                    label=f"facts/{episode_id[:8]}",
                )
                fact_list = facts.get("facts", [])
                metrics["facts_extracted"] = len(fact_list)
                await _record_extraction_cost(
                    namespace,
                    episode_id,
                    "facts",
                    _cost_model,
                    facts.get("_prompt_tokens", 0),
                    facts.get("_completion_tokens", 0),
                )
            except Exception as e:
                log.error("extraction.facts_failed", episode_id=episode_id, error=str(e))
                metrics["errors"].append(f"fact_extraction: {e}")
                fact_list = []

            # ── Step 4: Store facts with predicate validation ──
            for fact in fact_list:
                try:
                    await _store_fact(conn, fact, entity_map, namespace, episode_id, metrics)
                except Exception as e:
                    log.error("extraction.fact_store_failed", error=str(e))
                    metrics["errors"].append(f"fact_store: {e}")

        # ── Step 4b: Extract specific operational facts ──
        # Captures named resources, counts, IPs, CLI commands — things the
        # entity-predicate extractor misses. Stored in metadata['specific_facts']
        # and appended to every episode in the compiled output.
        try:
            sf_result = await _call_extraction_llm(
                SPECIFIC_FACT_EXTRACTION_PROMPT % content[:4000],
                label=f"specific_facts/{episode_id[:8]}",
            )
            specific_facts = sf_result.get("specific_facts", [])
            if specific_facts and isinstance(specific_facts, list):
                # Sanitize: keep only short strings, skip anything suspicious
                sanitized = [
                    str(f)[:200] for f in specific_facts if isinstance(f, str) and len(f) < 200
                ]
                if sanitized:
                    await conn.execute(
                        """UPDATE borg_episodes
                        SET metadata = jsonb_set(
                            COALESCE(metadata, '{}'),
                            '{specific_facts}',
                            $2::jsonb
                        )
                        WHERE id = $1""",
                        episode_id,
                        json.dumps(sanitized),
                    )
                    metrics["specific_facts_extracted"] = len(sanitized)
            await _record_extraction_cost(
                namespace,
                episode_id,
                "specific_facts",
                _cost_model,
                sf_result.get("_prompt_tokens", 0),
                sf_result.get("_completion_tokens", 0),
            )
        except Exception as e:
            log.error("extraction.specific_facts_failed", episode_id=episode_id, error=str(e))
            metrics["errors"].append(f"specific_fact_extraction: {e}")

        # ── Step 5: Mark episode as processed ──
        await conn.execute(
            "UPDATE borg_episodes SET processed = true WHERE id = $1",
            episode_id,
        )

        # ── Step 6: Extract candidate procedures ──
        try:
            entity_names_str = ", ".join(entity_map.keys()) if entity_map else "none"
            procedures = await _call_extraction_llm(
                PROCEDURE_EXTRACTION_PROMPT % (entity_names_str, content[:4000]),
                label=f"procedures/{episode_id[:8]}",
            )
            proc_list = procedures.get("procedures", [])
            for proc in proc_list:
                await _store_procedure(conn, proc, namespace, episode_id, metrics)
            await _record_extraction_cost(
                namespace,
                episode_id,
                "procedures",
                _cost_model,
                procedures.get("_prompt_tokens", 0),
                procedures.get("_completion_tokens", 0),
            )
        except Exception as e:
            log.error("extraction.procedures_failed", episode_id=episode_id, error=str(e))
            metrics["errors"].append(f"procedure_extraction: {e}")

    log.info("extraction.complete", episode_id=episode_id, metrics=metrics)
    return metrics


async def _store_procedure(conn, proc: dict, namespace: str, episode_id: str, metrics: dict):
    """Store or merge a candidate procedure."""
    decision = _evaluate_procedure_guardrails(proc)
    if decision.action == "reject":
        metrics["procedures_rejected_guardrail"] += 1
        log.warning(
            "extraction.procedure_rejected",
            pattern_preview=decision.pattern[:80],
            reason=decision.reject_reason,
        )
        return

    pattern = decision.pattern
    category = decision.category
    confidence = decision.confidence

    existing = await conn.fetchrow(
        """SELECT id, observation_count, confidence, source_episodes
        FROM borg_procedures
        WHERE LOWER(pattern) = LOWER($1)
          AND namespace = $2
          AND deleted_at IS NULL""",
        pattern,
        namespace,
    )

    if existing:
        new_count = existing["observation_count"] + 1
        new_confidence = (
            existing["confidence"] * existing["observation_count"] + confidence
        ) / new_count
        await conn.execute(
            """UPDATE borg_procedures
            SET observation_count = $2,
                confidence = $3,
                last_observed = now(),
                source_episodes = array_append(
                    COALESCE(source_episodes, '{}'), $4::uuid
                )
            WHERE id = $1""",
            existing["id"],
            new_count,
            round(new_confidence, 4),
            episode_id,
        )
        metrics["procedures_merged"] += 1
        log.info("extraction.procedure_merged", pattern=pattern[:60], count=new_count)
    else:
        await conn.execute(
            """INSERT INTO borg_procedures
            (pattern, category, namespace, source_episodes, confidence)
            VALUES ($1, $2, $3, ARRAY[$4::uuid], $5)""",
            pattern,
            category,
            namespace,
            episode_id,
            confidence,
        )
        metrics["procedures_extracted"] += 1
        log.info("extraction.procedure_new", pattern=pattern[:60], confidence=confidence)


async def _store_fact(
    conn, fact: dict, entity_map: dict, namespace: str, episode_id: str, metrics: dict
):
    """Store a single extracted fact with predicate validation and supersession check."""
    decision = _evaluate_fact_guardrails(fact, entity_map)
    if decision.action == "reject":
        metrics["facts_rejected_guardrail"] += 1
        log.warning(
            "extraction.fact_rejected",
            subject=decision.subject,
            predicate=decision.predicate,
            object=decision.object,
            reason=decision.reject_reason,
        )
        return

    subj_name = decision.subject
    pred = decision.predicate
    obj_name = decision.object
    is_custom = decision.custom
    evidence = decision.evidence

    subj_id = entity_map.get(subj_name)
    obj_id = entity_map.get(obj_name)
    if not subj_id or not obj_id:
        return

    if evidence == "explicit":
        metrics["evidence_explicit"] += 1
    else:
        metrics["evidence_implied"] += 1

    if is_custom:
        metrics["facts_custom_predicate"] += 1
        await _track_custom_predicate(conn, pred, episode_id)
    else:
        await conn.execute(
            "UPDATE borg_predicates SET usage_count = usage_count + 1 WHERE predicate = $1",
            pred,
        )

    status = "observed" if evidence == "explicit" else "extracted"
    properties = None
    if decision.action == "review":
        metrics["facts_review_required"] += 1
        properties = {
            "review_required": True,
            "review_reasons": list(decision.review_reasons),
        }
        log.warning(
            "extraction.fact_review_required",
            subject=subj_name,
            predicate=pred,
            object=obj_name,
            review_reasons=list(decision.review_reasons),
        )
    else:
        await _check_supersession(conn, subj_id, pred, obj_id, namespace)

    fact_id = await conn.fetchval(
        """INSERT INTO borg_facts
        (subject_id, object_id, predicate, namespace,
         source_episodes, evidence_status, valid_from, properties)
        VALUES ($1::uuid, $2::uuid, $3, $4, ARRAY[$5::uuid], $6, COALESCE($7::timestamptz, now()), $8::jsonb)
        RETURNING id""",
        subj_id,
        obj_id,
        pred,
        namespace,
        episode_id,
        status,
        decision.valid_from,
        json.dumps(properties) if properties else None,
    )

    await conn.execute(
        "INSERT INTO borg_fact_state (fact_id) VALUES ($1) ON CONFLICT DO NOTHING",
        fact_id,
    )


async def _record_extraction_cost(
    namespace: str,
    episode_id: str,
    step: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """Persist extraction token usage for cost tracking."""
    try:
        async with get_conn() as conn:
            await conn.execute(
                """INSERT INTO borg_extraction_costs
                   (namespace, episode_id, extraction_step, model, prompt_tokens, completion_tokens)
                   VALUES ($1, $2::uuid, $3, $4, $5, $6)""",
                namespace,
                episode_id,
                step,
                model,
                prompt_tokens,
                completion_tokens,
            )
    except Exception as e:
        log.warning("extraction.cost_record_failed", error=str(e), step=step)


# Maximum retries when the LLM returns an empty response
_LLM_MAX_RETRIES = 2


async def _call_extraction_llm(prompt: str, label: str = "extraction") -> dict:
    """Call OpenAI or Azure OpenAI for extraction. Returns parsed JSON.

    Default: standard OpenAI API.
    Azure opt-in: if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set.

    Compatible with both GPT-4.1 series (max_tokens, temperature) and
    GPT-5 series (max_completion_tokens, no temperature support).

    Retries up to _LLM_MAX_RETRIES times on empty responses.
    Logs request details, token usage, response content, and errors.
    """
    import time as _time

    # Determine client and model
    if settings.azure_openai_endpoint and settings.azure_openai_api_key:
        from openai import AsyncAzureOpenAI

        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version="2025-04-01-preview",
        )
        model = settings.azure_openai_extraction_deployment
    else:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        model = settings.openai_chat_model

    is_gpt5 = model.startswith("gpt-5")

    params = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a structured data extraction assistant. Always respond with valid JSON only. No preamble, no explanation, no markdown fences.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    if is_gpt5:
        params["max_completion_tokens"] = 4000
    else:
        params["max_tokens"] = 2000
        params["temperature"] = 0.0

    max_out = 4000 if is_gpt5 else 2000
    log.info(
        "extraction.llm_request",
        label=label,
        model=model,
        prompt_chars=len(prompt),
        prompt_tokens_est=len(prompt) // 4,
        max_completion_tokens=max_out,
    )

    for attempt in range(1 + _LLM_MAX_RETRIES):
        t0 = _time.monotonic()
        try:
            response = await client.chat.completions.create(**params)
        except Exception as e:
            log.error(
                "extraction.llm_api_error",
                label=label,
                model=model,
                attempt=attempt + 1,
                error_type=type(e).__name__,
            )
            if attempt < _LLM_MAX_RETRIES:
                continue
            raise

        elapsed_ms = int((_time.monotonic() - t0) * 1000)

        # Log token usage
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0
        finish_reason = response.choices[0].finish_reason if response.choices else "unknown"

        raw = response.choices[0].message.content if response.choices else None

        log.info(
            "extraction.llm_response",
            label=label,
            model=model,
            attempt=attempt + 1,
            elapsed_ms=elapsed_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
            response_chars=len(raw) if raw else 0,
        )

        # Check for token limit / context window issues
        if finish_reason == "length":
            log.error(
                "extraction.llm_truncated",
                label=label,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                max_completion_tokens=max_out,
                msg="Response truncated — output hit max_completion_tokens limit. "
                "Parsed JSON will likely be invalid. Consider increasing limit or reducing prompt.",
            )

        if finish_reason == "content_filter":
            log.error(
                "extraction.llm_content_filtered",
                label=label,
                model=model,
                prompt_tokens=prompt_tokens,
                msg="Response blocked by content filter",
            )
            if attempt < _LLM_MAX_RETRIES:
                continue
            return {}

        # Log if prompt is consuming most of the context window
        if prompt_tokens > 12000:
            log.warning(
                "extraction.llm_large_prompt",
                label=label,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                msg=f"Prompt used {prompt_tokens} tokens — may be approaching context window limit",
            )

        if not raw:
            if attempt < _LLM_MAX_RETRIES:
                log.warning(
                    "extraction.llm_empty_response",
                    label=label,
                    model=model,
                    attempt=attempt + 1,
                    max_retries=_LLM_MAX_RETRIES,
                    msg="Empty response, retrying",
                )
                continue
            log.error(
                "extraction.llm_empty_exhausted",
                label=label,
                model=model,
                attempts=1 + _LLM_MAX_RETRIES,
                prompt_tokens=prompt_tokens,
            )
            return {}

        text = raw.strip()

        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        if not text:
            if attempt < _LLM_MAX_RETRIES:
                log.warning(
                    "extraction.llm_empty_after_strip",
                    label=label,
                    model=model,
                    attempt=attempt + 1,
                    msg="Response empty after stripping fences, retrying",
                )
                continue
            log.error(
                "extraction.llm_empty_after_strip_exhausted",
                label=label,
                model=model,
                response_chars=len(raw),
            )
            return {}

        try:
            parsed = json.loads(text)
            log.info(
                "extraction.llm_parsed",
                label=label,
                keys=list(parsed.keys()) if isinstance(parsed, dict) else "non-dict",
                items=len(
                    parsed.get("entities", parsed.get("facts", parsed.get("procedures", [])))
                ),
            )
            if isinstance(parsed, dict):
                parsed["_prompt_tokens"] = prompt_tokens
                parsed["_completion_tokens"] = completion_tokens
            return parsed
        except json.JSONDecodeError as e:
            log.error(
                "extraction.llm_json_parse_failed",
                label=label,
                model=model,
                error_type=type(e).__name__,
                response_chars=len(text),
            )
            if attempt < _LLM_MAX_RETRIES:
                log.warning(
                    "extraction.llm_parse_retry",
                    label=label,
                    attempt=attempt + 1,
                    msg="JSON parse failed, retrying",
                )
                continue
            raise

    # Should not reach here, but just in case
    return {}


async def _track_custom_predicate(conn, predicate: str, episode_id: str):
    """Track a non-canonical predicate for review."""
    existing = await conn.fetchrow(
        "SELECT id, occurrences FROM borg_predicate_candidates WHERE predicate = $1 AND resolved_at IS NULL",
        predicate,
    )
    if existing:
        await conn.execute(
            """UPDATE borg_predicate_candidates
            SET occurrences = occurrences + 1,
                example_facts = array_append(COALESCE(example_facts, '{}'), $2::uuid)
            WHERE id = $1""",
            existing["id"],
            episode_id,
        )
    else:
        await conn.execute(
            """INSERT INTO borg_predicate_candidates (predicate, example_facts)
            VALUES ($1, ARRAY[$2::uuid])""",
            predicate,
            episode_id,
        )


async def _check_supersession(
    conn, subject_id: str, predicate: str, new_object_id: str, namespace: str
):
    """If a new fact contradicts an existing current fact, supersede the old one."""
    existing = await conn.fetchrow(
        """SELECT id, object_id FROM borg_facts
        WHERE subject_id = $1::uuid
          AND predicate = $2
          AND namespace = $3
          AND valid_until IS NULL
          AND deleted_at IS NULL
          AND object_id != $4::uuid""",
        subject_id,
        predicate,
        namespace,
        new_object_id,
    )
    if existing:
        await conn.execute(
            """UPDATE borg_facts
            SET valid_until = now(),
                evidence_status = 'superseded'
            WHERE id = $1""",
            existing["id"],
        )
        log.info(
            "extraction.supersession",
            old_fact=str(existing["id"]),
            predicate=predicate,
            old_object=str(existing["object_id"]),
            new_object=new_object_id,
        )
