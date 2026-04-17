"""LLM-as-judge evaluator for benchmark results.

Scores each condition's response against the 7 spec metrics using a
structured evaluation prompt. Returns JSON scores per metric.

Metrics:
  1. task_success        — Did the LLM produce a correct, useful response? (0 or 1)
  2. retrieval_precision — % of injected context items that were actually needed (0.0-1.0)
  3. stale_fact_rate     — % of injected items that were outdated or superseded (0.0-1.0)
  4. irrelevant_rate     — % of injected items unrelated to the task (0.0-1.0)
  5. context_tokens      — Total tokens injected (integer, from run data)
  6. latency_ms          — End-to-end latency (integer, from run data)
  7. explainability      — Can the audit log explain selections? (0 or 1, C only)
"""

import json
import re

from bench.config import cfg
from bench.llm import call_llm

JUDGE_SYSTEM = (
    "You are an expert evaluator assessing the quality of AI-generated responses. "
    "You evaluate based on specific criteria and return structured JSON scores. "
    "Be rigorous and consistent. You MUST respond with valid JSON only — no preamble, "
    "no explanation outside the JSON object, no markdown fences."
)

JUDGE_PROMPT = """Evaluate this AI response for the given task.

## Task
Query: {query}
Task type: {task_class}
Description: {description}

## Ground Truth
{ground_truth}

## Expected Knowledge
The response should demonstrate awareness of:
{expected_knowledge}

## Context Provided to the AI
{context_summary}

## AI Response
{response}

---

Score the response on these metrics. Return ONLY a single JSON object. No text before or after it.

{{
  "task_success": <0 or 1>,
  "task_success_reasoning": "<1-2 sentences>",
  "retrieval_precision": <0.0 to 1.0>,
  "retrieval_precision_reasoning": "<1-2 sentences>",
  "stale_fact_rate": <0.0 to 1.0>,
  "stale_fact_reasoning": "<1-2 sentences>",
  "irrelevant_rate": <0.0 to 1.0>,
  "irrelevant_reasoning": "<1-2 sentences>",
  "knowledge_coverage": <0.0 to 1.0>,
  "knowledge_coverage_reasoning": "<1-2 sentences>"
}}
"""

MAX_JUDGE_RETRIES = 2


def _format_expected_knowledge(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _summarize_context(run_result: dict) -> str:
    ctx = run_result.get("context_injected")
    if not ctx:
        return "No context was provided (condition A: no memory)."
    tokens = run_result.get("context_tokens", 0)
    condition = run_result.get("condition", "?")
    if condition == "B":
        n = run_result.get("episodes_fetched", "?")
        return f"Condition B: {n} raw episodes injected as unstructured text ({tokens} tokens).\n\nContext:\n{ctx[:3000]}"
    elif condition == "C":
        return f"Condition C: Borg-compiled context ({tokens} tokens).\n\nContext:\n{ctx[:3000]}"
    return f"Context ({tokens} tokens):\n{ctx[:3000]}"


def _extract_json(text: str) -> dict | None:
    """Try multiple strategies to extract valid JSON from LLM output."""
    text = text.strip()

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # Strategy 3: find first { ... last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Strategy 4: regex for JSON-like block
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return None


async def evaluate(task: dict, run_result: dict) -> dict:
    """Evaluate a single run result using LLM-as-judge.

    Retries up to MAX_JUDGE_RETRIES times on parse failure.
    Returns a dict with all metric scores plus reasoning.
    """
    prompt = JUDGE_PROMPT.format(
        query=task["query"],
        task_class=task.get("task_class", "unknown"),
        description=task.get("description", ""),
        ground_truth=task.get("ground_truth", "No ground truth provided."),
        expected_knowledge=_format_expected_knowledge(
            task.get("expected_knowledge", [])
        ),
        context_summary=_summarize_context(run_result),
        response=run_result.get("response", "") or "(empty response)",
    )

    scores = None
    last_raw = ""

    for attempt in range(1 + MAX_JUDGE_RETRIES):
        raw = await call_llm(
            prompt=prompt,
            system=JUDGE_SYSTEM,
            model=cfg.judge_model,
            max_tokens=4000,
        )
        last_raw = raw

        parsed = _extract_json(raw)
        if parsed and "task_success" in parsed:
            scores = parsed
            break

    if scores is None:
        scores = {
            "task_success": 0,
            "task_success_reasoning": f"Judge parse error after {1 + MAX_JUDGE_RETRIES} attempts: {last_raw[:300]}",
            "retrieval_precision": 0.0,
            "retrieval_precision_reasoning": "Parse error",
            "stale_fact_rate": 0.0,
            "stale_fact_reasoning": "Parse error",
            "irrelevant_rate": 0.0,
            "irrelevant_reasoning": "Parse error",
            "knowledge_coverage": 0.0,
            "knowledge_coverage_reasoning": "Parse error",
            "parse_error": True,
            "retries": 1 + MAX_JUDGE_RETRIES,
        }

    # Merge in non-LLM metrics from run data
    scores["context_tokens"] = run_result.get("context_tokens", 0)
    scores["latency_ms"] = run_result.get("latency_ms", 0)
    scores["condition"] = run_result.get("condition", "?")
    scores["task_id"] = run_result.get("task_id", "?")

    # Explainability: only meaningful for condition C (has audit trace)
    if run_result.get("condition") == "C":
        scores["explainability"] = 1 if run_result.get("candidates_found", 0) > 0 else 0
    else:
        scores["explainability"] = None

    return scores
