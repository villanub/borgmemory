"""Condition B: Simple retrieval — top-N vector-similar episodes as raw text.

Bypasses the Borg compiler entirely. Hits pgvector directly to get the
same episodes that Borg's episode_recall strategy would find, but injects
them as unstructured text with no ranking, no memory-type weighting, and
no compilation.
"""

import time

import asyncpg

from bench.config import cfg
from bench.llm import call_llm

SYSTEM_PROMPT = (
    "You are a senior cloud architect and AI modernization lead. "
    "You have access to relevant past conversations provided below. "
    "Use them to answer the question accurately. "
    "If the provided context doesn't help, say so."
)


async def _fetch_episodes(query: str, namespace: str, limit: int) -> list[dict]:
    """Fetch top-N similar episodes via direct pgvector query.

    Generates a query embedding via Azure OpenAI, then runs cosine
    similarity search against borg_episodes. Falls back to recency
    if embedding generation fails.
    """
    conn = await asyncpg.connect(cfg.database_url)
    try:
        # Generate query embedding
        emb = None
        try:
            from openai import AsyncAzureOpenAI
            client = AsyncAzureOpenAI(
                azure_endpoint=cfg.azure_endpoint,
                api_key=cfg.azure_api_key,
                api_version="2025-04-01-preview",
            )
            # Use the same embedding endpoint as Borg
            emb_key = cfg.azure_api_key
            import os
            if os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"):
                from openai import AsyncAzureOpenAI as EmbClient
                client = EmbClient(
                    azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
                    api_key=os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY", emb_key),
                    api_version="2025-04-01-preview",
                )
            resp = await client.embeddings.create(
                model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
                input=query,
            )
            emb = resp.data[0].embedding
        except Exception:
            emb = None

        if emb:
            rows = await conn.fetch(
                """SELECT id, source, content, occurred_at,
                          1 - (embedding <=> $1::vector) as similarity
                FROM borg_episodes
                WHERE namespace = $2 AND deleted_at IS NULL
                  AND embedding IS NOT NULL AND processed = true
                ORDER BY embedding <=> $1::vector
                LIMIT $3""",
                str(emb), namespace, limit,
            )
        else:
            # Recency fallback
            rows = await conn.fetch(
                """SELECT id, source, content, occurred_at, NULL as similarity
                FROM borg_episodes
                WHERE namespace = $1 AND deleted_at IS NULL AND processed = true
                ORDER BY occurred_at DESC
                LIMIT $2""",
                namespace, limit,
            )

        return [
            {
                "id": str(r["id"]),
                "source": r["source"],
                "content": r["content"],
                "occurred_at": r["occurred_at"].isoformat() if r["occurred_at"] else None,
                "similarity": round(float(r["similarity"]), 4) if r["similarity"] else None,
            }
            for r in rows
        ]
    finally:
        await conn.close()


def _format_context(episodes: list[dict]) -> str:
    """Format episodes as raw text block for injection."""
    parts = []
    for i, ep in enumerate(episodes, 1):
        dt = ep["occurred_at"][:10] if ep["occurred_at"] else "unknown"
        sim = f" (similarity: {ep['similarity']})" if ep["similarity"] else ""
        parts.append(f"--- Episode {i} [{ep['source']} {dt}]{sim} ---")
        parts.append(ep["content"])
        parts.append("")
    return "\n".join(parts)


async def run(task: dict) -> dict:
    """Run condition B: top-N vector episodes injected as raw text."""
    query = task["query"]
    namespace = cfg.namespace

    # Fetch episodes directly from pgvector
    t0 = time.monotonic()
    episodes = await _fetch_episodes(query, namespace, cfg.condition_b_limit)
    fetch_ms = int((time.monotonic() - t0) * 1000)

    context = _format_context(episodes)
    context_tokens = len(context) // 4  # rough estimate

    # Build prompt with raw context
    prompt = f"""Here are relevant past conversations:

{context}

Based on the above context, answer this question:
{query}"""

    t1 = time.monotonic()
    response = await call_llm(prompt=prompt, system=SYSTEM_PROMPT, label=f"B/{task['id']}")
    llm_ms = int((time.monotonic() - t1) * 1000)

    return {
        "condition": "B",
        "task_id": task["id"],
        "response": response,
        "context_injected": context,
        "context_tokens": context_tokens,
        "episodes_fetched": len(episodes),
        "latency_ms": fetch_ms + llm_ms,
        "latency_fetch_ms": fetch_ms,
        "latency_llm_ms": llm_ms,
    }
