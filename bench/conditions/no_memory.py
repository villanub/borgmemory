"""Condition A: No memory — raw LLM call with no context."""

import time

from bench.llm import call_llm

SYSTEM_PROMPT = (
    "You are a senior cloud architect and AI modernization lead. "
    "Answer the question based on your general knowledge. "
    "If you don't have specific information, say so."
)


async def run(task: dict) -> dict:
    """Run condition A: LLM with no Borg context."""
    query = task["query"]
    t0 = time.monotonic()
    response = await call_llm(prompt=query, system=SYSTEM_PROMPT, label=f"A/{task['id']}")
    latency_ms = int((time.monotonic() - t0) * 1000)

    return {
        "condition": "A",
        "task_id": task["id"],
        "response": response,
        "context_injected": None,
        "context_tokens": 0,
        "latency_ms": latency_ms,
    }
