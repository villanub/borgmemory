"""Borg episode ingestion — offline pipeline."""

import hashlib
import json
from datetime import datetime, timezone

from borg.db import get_conn
from borg.models import EpisodeCreate, EpisodeResponse


async def ingest_episode(ep: EpisodeCreate) -> EpisodeResponse:
    """Ingest a new episode into Borg. Returns immediately; extraction is async."""
    content_hash = hashlib.sha256(ep.content.encode()).hexdigest()
    occurred_at = ep.occurred_at or datetime.now(timezone.utc)

    async with get_conn() as conn:
        # Check idempotency: content hash
        existing = await conn.fetchval(
            "SELECT id FROM borg_episodes WHERE content_hash = $1 AND namespace = $2 AND deleted_at IS NULL",
            content_hash,
            ep.namespace,
        )
        if existing:
            return EpisodeResponse(episode_id=existing, status="duplicate")

        # Check idempotency: source_event_id
        if ep.source_event_id:
            existing = await conn.fetchval(
                "SELECT id FROM borg_episodes WHERE source = $1 AND source_event_id = $2",
                ep.source,
                ep.source_event_id,
            )
            if existing:
                return EpisodeResponse(episode_id=existing, status="duplicate")

        # Insert episode
        episode_id = await conn.fetchval(
            """INSERT INTO borg_episodes
            (source, source_id, source_event_id, content, content_hash,
             occurred_at, namespace, metadata, participants, processed)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, false)
            RETURNING id""",
            ep.source,
            ep.source_id,
            ep.source_event_id,
            ep.content,
            content_hash,
            occurred_at,
            ep.namespace,
            json.dumps(ep.metadata),
            ep.participants,
        )

        return EpisodeResponse(episode_id=episode_id, status="accepted")
