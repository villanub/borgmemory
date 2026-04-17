"""Condition C: Borg compiled — full online pipeline via borg_think."""

import time

import httpx

from bench.config import cfg
from bench.llm import call_llm

SYSTEM_PROMPT = (
    "You are a senior cloud architect and AI modernization lead. "
    "You have access to compiled professional context provided below. "
    "This context has been curated and ranked by relevance. "
    "Use it to answer the question accurately. "
    "If the provided context doesn't help, say so."
)


async def _call_borg_think(query: str, namespace: str, task_hint: str | None) -> dict:
    """Call POST /api/think and return the response + audit data."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        body = {
            "query": query,
            "namespace": namespace,
            "model": "gpt",  # compact JSON format — matches GPT-5-mini task model
        }
        if task_hint:
            body["task_hint"] = task_hint

        resp = await client.post(
            f"{cfg.borg_url}/api/think",
            json=body,
        )
        resp.raise_for_status()
        return resp.json()


async def _get_audit_trace(namespace: str) -> dict | None:
    """Fetch the most recent audit log entry for analysis."""
    # TODO: query audit log when endpoint exists
    return None


async def run(task: dict) -> dict:
    """Run condition C: full Borg compilation pipeline."""
    query = task["query"]
    namespace = cfg.namespace
    task_hint = task.get("task_class")

    # Call borg_think
    t0 = time.monotonic()
    think_resp = _call_borg_think(query, namespace, task_hint)
    think_resp = await think_resp
    think_ms = int((time.monotonic() - t0) * 1000)

    compiled_context = think_resp.get("compiled_context", "")
    context_tokens = think_resp.get("tokens", 0)

    # Build prompt with compiled context
    prompt = f"""Here is compiled professional context relevant to your task:

{compiled_context}

Based on the above context, answer this question:
{query}"""

    t1 = time.monotonic()
    response = await call_llm(prompt=prompt, system=SYSTEM_PROMPT, label=f"C/{task['id']}")
    llm_ms = int((time.monotonic() - t1) * 1000)

    return {
        "condition": "C",
        "task_id": task["id"],
        "response": response,
        "context_injected": compiled_context,
        "context_tokens": context_tokens,
        "task_class": think_resp.get("task_class", ""),
        "candidates_found": think_resp.get("candidates_found", 0),
        "candidates_selected": think_resp.get("candidates_selected", 0),
        "latency_ms": think_ms + llm_ms,
        "latency_think_ms": think_ms,
        "latency_llm_ms": llm_ms,
        "borg_latency_ms": think_resp.get("latency_ms", 0),
    }
