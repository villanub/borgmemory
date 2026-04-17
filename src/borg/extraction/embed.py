"""Borg embedding service — generate and store vector embeddings.

Default: standard OpenAI embeddings (openai_api_key required).
Optional: Azure OpenAI for embeddings when AZURE_OPENAI_ENDPOINT and
AZURE_OPENAI_API_KEY are set.

Episodes without embeddings fall back to recency-based retrieval.
Supports a separate Azure OpenAI resource for embeddings via
AZURE_OPENAI_EMBEDDING_ENDPOINT. If not set, uses the main
AZURE_OPENAI_ENDPOINT.
"""

import structlog

from borg.config import settings

log = structlog.get_logger()

_client = None
_unavailable = False


def _get_client():
    """Get or create the embedding client.

    Default: AsyncOpenAI with standard OpenAI API.
    Azure opt-in: If AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set,
    uses AsyncAzureOpenAI instead. Can optionally use embedding-specific
    endpoint/key (AZURE_OPENAI_EMBEDDING_ENDPOINT).
    """
    global _client, _unavailable
    if _unavailable:
        return None
    if _client is None:
        # Check if Azure OpenAI is configured (opt-in)
        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            # Use embedding-specific endpoint/key if set, else fall back to main
            endpoint = settings.azure_openai_embedding_endpoint or settings.azure_openai_endpoint
            api_key = settings.azure_openai_embedding_api_key or settings.azure_openai_api_key

            from openai import AsyncAzureOpenAI

            _client = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version="2024-06-01",
            )
            log.info(
                "embedding.client_created",
                provider="azure",
                endpoint=endpoint[:50] + "...",
                deployment=settings.azure_openai_embedding_deployment,
            )
        else:
            # Default: standard OpenAI
            if not settings.openai_api_key:
                log.warning(
                    "embedding.not_configured",
                    msg="OpenAI API key not configured. "
                    "Set OPENAI_API_KEY to enable embeddings.",
                )
                _unavailable = True
                return None

            from openai import AsyncOpenAI

            _client = AsyncOpenAI(api_key=settings.openai_api_key)
            log.info(
                "embedding.client_created",
                provider="openai",
                model=settings.openai_embedding_model,
            )
    return _client


async def generate_embedding(text: str) -> list[float]:
    """Generate a 1536-dim embedding via OpenAI or Azure OpenAI."""
    client = _get_client()
    if client is None:
        raise RuntimeError("Embedding service not configured")

    model = (
        settings.azure_openai_embedding_deployment
        if settings.azure_openai_endpoint
        else settings.openai_embedding_model
    )

    truncated = text[:32000]
    try:
        response = await client.embeddings.create(
            model=model,
            input=truncated,
        )
        return response.data[0].embedding
    except Exception as e:
        log.error(
            "embedding.failed",
            error=str(e),
            text_length=len(text),
            deployment=settings.azure_openai_embedding_deployment,
        )
        raise


async def embed_episode(episode_id, conn) -> bool:
    """Generate and store embedding for an episode."""
    row = await conn.fetchrow(
        "SELECT id, content FROM borg_episodes WHERE id = $1 AND embedding IS NULL AND deleted_at IS NULL",
        episode_id,
    )
    if not row:
        return False

    try:
        embedding = await generate_embedding(row["content"])
        await conn.execute(
            "UPDATE borg_episodes SET embedding = $1 WHERE id = $2",
            str(embedding),
            episode_id,
        )
        log.info("embedding.stored", episode_id=str(episode_id))
        return True
    except RuntimeError:
        return False
    except Exception as e:
        log.error("embedding.episode_failed", episode_id=str(episode_id), error=str(e))
        return False
