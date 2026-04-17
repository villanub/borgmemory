"""Borg background worker — processes unprocessed episodes asynchronously.

This is the offline pipeline. It runs continuously in the background,
picks up episodes that have been ingested but not yet processed,
generates embeddings, extracts entities and facts, and marks them done.

The online pipeline (borg_think) never waits for this. They share a
database but not a runtime.

Gap 4: Also runs periodic hot-tier snapshots (every 24 hours).

Graceful degradation:
- Without Azure OpenAI: episodes are marked processed with no extraction.
  They remain searchable by recency. When credentials are added later,
  unprocessed episodes can be requeued.
- With Azure OpenAI: full pipeline runs (embed → extract → resolve → facts → procedures).
"""

import asyncio
import json

import structlog

from borg.db import get_conn
from borg.extraction.embed import embed_episode
from borg.extraction.pipeline import extract_episode

log = structlog.get_logger()

# How often to poll for unprocessed episodes (seconds)
POLL_INTERVAL = 5
# Max episodes to process per batch
BATCH_SIZE = 5
# Max consecutive errors before backing off
MAX_CONSECUTIVE_ERRORS = 3
# Backoff duration after repeated errors (seconds)
ERROR_BACKOFF = 60
# Snapshot interval (seconds) — 24 hours
SNAPSHOT_INTERVAL = 86400

_running = False
_snapshot_task: asyncio.Task | None = None


def _safe_error_summary(exc: Exception) -> str:
    return type(exc).__name__


async def start_worker():
    """Start the background extraction worker loop."""
    global _running, _snapshot_task
    _running = True
    consecutive_errors = 0

    # Launch snapshot task alongside extraction worker
    _snapshot_task = asyncio.create_task(_snapshot_loop())

    log.info("worker.started", poll_interval=POLL_INTERVAL, batch_size=BATCH_SIZE)

    while _running:
        try:
            processed = await _process_batch()

            if processed > 0:
                consecutive_errors = 0  # Reset on success
                log.info("worker.batch_complete", episodes_processed=processed)
                await asyncio.sleep(0.5)  # Brief pause then check for more
            else:
                await asyncio.sleep(POLL_INTERVAL)

        except asyncio.CancelledError:
            log.info("worker.cancelled")
            break
        except Exception as e:
            consecutive_errors += 1
            log.error(
                "worker.error",
                error_type=type(e).__name__,
                consecutive_errors=consecutive_errors,
            )
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                log.warning(
                    "worker.backoff",
                    msg=f"Too many errors, backing off for {ERROR_BACKOFF}s",
                )
                await asyncio.sleep(ERROR_BACKOFF)
                consecutive_errors = 0
            else:
                await asyncio.sleep(POLL_INTERVAL)


async def stop_worker():
    """Signal the worker to stop."""
    global _running, _snapshot_task
    _running = False
    if _snapshot_task:
        _snapshot_task.cancel()
        try:
            await _snapshot_task
        except asyncio.CancelledError:
            pass
        _snapshot_task = None
    log.info("worker.stopping")


async def _snapshot_loop():
    """Periodic hot-tier snapshot writer (Gap 4).

    Writes snapshots for all namespaces every SNAPSHOT_INTERVAL seconds.
    First snapshot fires after one interval (not immediately on startup).
    """
    log.info("snapshot.loop_started", interval_hours=SNAPSHOT_INTERVAL / 3600)

    while _running:
        try:
            await asyncio.sleep(SNAPSHOT_INTERVAL)
            if not _running:
                break

            from borg.snapshots import write_all_snapshots

            results = await write_all_snapshots()
            log.info("snapshot.cycle_complete", namespaces=len(results))

        except asyncio.CancelledError:
            log.info("snapshot.loop_cancelled")
            break
        except Exception as e:
            log.error("snapshot.loop_error", error_type=type(e).__name__)
            # Don't crash the snapshot loop on error, just wait and retry
            await asyncio.sleep(60)


async def _process_batch() -> int:
    """Pick up unprocessed episodes and run the offline pipeline.

    Per-episode pipeline:
    1. Generate embedding (for vector search)
    2. Extract entities (LLM call → three-pass resolution)
    3. Extract facts (LLM call → predicate validation → supersession)
    4. Extract procedures (LLM call → merge or create)
    5. Mark episode processed

    Returns number of episodes processed in this batch.
    """
    async with get_conn() as conn:
        rows = await conn.fetch(
            """SELECT id, namespace, source, LENGTH(content) as content_length
            FROM borg_episodes
            WHERE processed = false
              AND deleted_at IS NULL
            ORDER BY ingested_at ASC
            LIMIT $1""",
            BATCH_SIZE,
        )

    if not rows:
        return 0

    processed_count = 0

    for row in rows:
        episode_id = row["id"]
        ep_str = str(episode_id)

        try:
            log.info(
                "worker.processing",
                episode_id=ep_str,
                namespace=row["namespace"],
                source=row["source"],
                content_length=row["content_length"],
            )

            # Step 1: Generate embedding
            async with get_conn() as conn:
                embedded = await embed_episode(episode_id, conn)
                if embedded:
                    log.info("worker.embedded", episode_id=ep_str)
                else:
                    log.info("worker.embed_skipped", episode_id=ep_str)

            # Steps 2-5: Full extraction pipeline
            # (entities, resolution, facts, supersession, procedures, mark processed)
            metrics = await extract_episode(ep_str)

            # Log extraction metrics to audit
            async with get_conn() as conn:
                await conn.execute(
                    """INSERT INTO borg_audit_log
                    (task_class, namespace, retrieval_profile, extraction_metrics)
                    VALUES ('extraction', $1, 'offline_pipeline', $2)""",
                    row["namespace"],
                    json.dumps(metrics),
                )

            processed_count += 1

            log.info(
                "worker.episode_complete",
                episode_id=ep_str,
                entities_extracted=metrics.get("entities_extracted", 0),
                entities_resolved=metrics.get("entities_resolved", 0),
                entities_new=metrics.get("entities_new", 0),
                facts_extracted=metrics.get("facts_extracted", 0),
                custom_predicates=metrics.get("facts_custom_predicate", 0),
                procedures_extracted=metrics.get("procedures_extracted", 0),
                procedures_merged=metrics.get("procedures_merged", 0),
                errors=len(metrics.get("errors", [])),
                skipped=metrics.get("skipped_no_llm", False),
            )

        except Exception as e:
            log.error("worker.episode_failed", episode_id=ep_str, error_type=type(e).__name__)
            # Mark as processed with error metadata to prevent infinite retry.
            # To retry later: UPDATE borg_episodes SET processed = false WHERE id = '...'
            try:
                async with get_conn() as conn:
                    await conn.execute(
                        """UPDATE borg_episodes
                        SET processed = true,
                            metadata = jsonb_set(
                                COALESCE(metadata, '{}'),
                                '{extraction_error}',
                                to_jsonb($2::text)
                            )
                        WHERE id = $1""",
                        episode_id,
                        _safe_error_summary(e),
                    )
            except Exception as inner_e:
                log.error(
                    "worker.mark_failed_error",
                    episode_id=ep_str,
                    error_type=type(inner_e).__name__,
                )

    return processed_count


async def process_single_episode(episode_id: str) -> dict:
    """Process a single episode on-demand (for testing or manual trigger).

    Unlike the batch worker, this runs synchronously and returns metrics.
    """
    log.info("worker.manual_process", episode_id=episode_id)

    # Step 1: Embed
    async with get_conn() as conn:
        await embed_episode(episode_id, conn)

    # Steps 2-5: Extract
    metrics = await extract_episode(episode_id)

    return metrics


async def requeue_failed_episodes(namespace: str | None = None) -> int:
    """Requeue episodes that failed extraction (have extraction_error in metadata).

    Useful when fixing extraction bugs or adding Azure OpenAI credentials.
    Returns count of requeued episodes.
    """
    async with get_conn() as conn:
        if namespace:
            result = await conn.execute(
                """UPDATE borg_episodes
                SET processed = false,
                    metadata = metadata - 'extraction_error'
                WHERE processed = true
                  AND deleted_at IS NULL
                  AND namespace = $1
                  AND metadata ? 'extraction_error'""",
                namespace,
            )
        else:
            result = await conn.execute(
                """UPDATE borg_episodes
                SET processed = false,
                    metadata = metadata - 'extraction_error'
                WHERE processed = true
                  AND deleted_at IS NULL
                  AND metadata ? 'extraction_error'""",
            )

        count = int(result.split()[-1]) if result else 0
        log.info("worker.requeued", count=count, namespace=namespace)
        return count


async def trigger_snapshot(namespace: str | None = None) -> list[dict]:
    """Manually trigger a snapshot (for admin endpoint).

    If namespace is provided, snapshot only that namespace.
    Otherwise snapshot all namespaces.
    """
    from borg.snapshots import write_all_snapshots, write_snapshot

    if namespace:
        result = await write_snapshot(namespace)
        return [result]
    else:
        return await write_all_snapshots()
