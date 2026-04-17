"""Backfill specific_facts extraction for existing processed episodes.

Runs the SPECIFIC_FACT_EXTRACTION_PROMPT on episodes that don't yet have
metadata['specific_facts'], storing results without touching other extraction
artifacts (entities, facts, procedures).

Usage:
    python3 scripts/backfill_specific_facts.py [--namespace azure-msp] [--limit 50] [--dry-run]
"""

import argparse
import asyncio
import json
import os
import sys

# Ensure src/ is on the path when run from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import structlog
from dotenv import load_dotenv

from borg.extraction.pipeline import _call_extraction_llm
from borg.extraction.prompts import SPECIFIC_FACT_EXTRACTION_PROMPT

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

log = structlog.get_logger()


async def backfill(namespace: str | None, limit: int, dry_run: bool, concurrency: int = 5) -> None:
    import asyncio

    import asyncpg

    db_url = os.getenv(
        "BENCH_DATABASE_URL",
        "postgresql://borg:borg_password@localhost:5433/borg",
    )
    conn = await asyncpg.connect(db_url)
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=concurrency + 1)

    if namespace:
        rows = await conn.fetch(
            """SELECT id, content, namespace
               FROM borg_episodes
               WHERE processed = true
                 AND deleted_at IS NULL
                 AND (metadata IS NULL OR metadata->'specific_facts' IS NULL)
                 AND namespace = $1
               ORDER BY occurred_at DESC
               LIMIT $2""",
            namespace,
            limit,
        )
    else:
        rows = await conn.fetch(
            """SELECT id, content, namespace
               FROM borg_episodes
               WHERE processed = true
                 AND deleted_at IS NULL
                 AND (metadata IS NULL OR metadata->'specific_facts' IS NULL)
               ORDER BY occurred_at DESC
               LIMIT $1""",
            limit,
        )

    await conn.close()
    print(f"Found {len(rows)} episodes to backfill (concurrency={concurrency})")

    results = {"ok": 0, "skipped": 0, "errors": 0}
    sem = asyncio.Semaphore(concurrency)

    async def process_row(row):
        episode_id = str(row["id"])
        content = row["content"]
        ns = row["namespace"]
        async with sem:
            try:
                result = await _call_extraction_llm(
                    SPECIFIC_FACT_EXTRACTION_PROMPT % content[:4000],
                    label=f"backfill/{episode_id[:8]}",
                )
                specific_facts = result.get("specific_facts", [])
                if not specific_facts or not isinstance(specific_facts, list):
                    results["skipped"] += 1
                    print(f"  {episode_id[:8]} [{ns}] — no specific facts found")
                    return

                sanitized = [
                    str(f)[:200] for f in specific_facts if isinstance(f, str) and len(f) < 200
                ]

                if dry_run:
                    print(f"  {episode_id[:8]} [{ns}] DRY RUN — would store {len(sanitized)} facts")
                else:
                    async with pool.acquire() as db:
                        await db.execute(
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
                    print(f"  {episode_id[:8]} [{ns}] — stored {len(sanitized)} specific facts")
                results["ok"] += 1

            except Exception as e:
                results["errors"] += 1
                print(f"  {episode_id[:8]} [{ns}] ERROR: {e}")

    await asyncio.gather(*[process_row(row) for row in rows])
    await pool.close()
    print(
        f"\nDone: {results['ok']} updated, {results['skipped']} skipped (no facts), {results['errors']} errors"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", default=None, help="Limit to one namespace")
    parser.add_argument("--limit", type=int, default=50, help="Max episodes to process")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    parser.add_argument("--concurrency", type=int, default=5, help="Parallel LLM calls")
    args = parser.parse_args()

    asyncio.run(backfill(args.namespace, args.limit, args.dry_run, args.concurrency))


if __name__ == "__main__":
    main()
