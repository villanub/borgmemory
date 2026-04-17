"""Pydantic models for Borg data types.

These models serve double duty:
  1. Runtime validation for request/response data
  2. OpenAPI schema generation for Swagger docs
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from borg.config import settings
from borg.namespaces import NamespaceStr

# ══════════════════════════════════════════════
# Enums (used in schemas for OpenAPI dropdown hints)
# ══════════════════════════════════════════════


class MemoryType(str, Enum):
    semantic = "semantic"
    episodic = "episodic"
    procedural = "procedural"


class TaskHint(str, Enum):
    debug = "debug"
    architecture = "architecture"
    compliance = "compliance"
    writing = "writing"
    chat = "chat"


class TargetModel(str, Enum):
    claude = "claude"
    gpt = "gpt"
    local = "local"
    copilot = "copilot"


def normalize_target_model(value: Any) -> Any:
    """Map specific model IDs to Borg's output-format families."""
    if value is None or isinstance(value, TargetModel):
        return value
    if not isinstance(value, str):
        return value

    normalized = value.strip().lower()
    if not normalized:
        return None

    if normalized in TargetModel._value2member_map_:
        return normalized

    prefixes = {
        "claude": TargetModel.claude,
        "gpt": TargetModel.gpt,
        "chatgpt": TargetModel.gpt,
        "codex": TargetModel.gpt,
        "o1": TargetModel.gpt,
        "o3": TargetModel.gpt,
        "o4": TargetModel.gpt,
        "copilot": TargetModel.copilot,
        "github-copilot": TargetModel.copilot,
        "local": TargetModel.local,
        "llama": TargetModel.local,
        "mistral": TargetModel.local,
        "ollama": TargetModel.local,
        "qwen": TargetModel.local,
        "deepseek": TargetModel.local,
    }
    for prefix, target in prefixes.items():
        if normalized.startswith(prefix):
            return target

    return value


class EvidenceStatus(str, Enum):
    user_asserted = "user_asserted"
    observed = "observed"
    extracted = "extracted"
    inferred = "inferred"
    promoted = "promoted"
    deprecated = "deprecated"
    superseded = "superseded"


class ProcedureStatus(str, Enum):
    extracted = "extracted"
    promoted = "promoted"
    deprecated = "deprecated"


class Tier(str, Enum):
    hot = "hot"
    warm = "warm"


# ══════════════════════════════════════════════
# Episodes
# ══════════════════════════════════════════════


class EpisodeCreate(BaseModel):
    """Ingest a new episode into Borg."""

    content: str = Field(
        ...,
        description="The text content of the episode (conversation, decision, note)",
        max_length=settings.borg_max_episode_content_chars,
    )
    source: str = Field(
        ...,
        description="Origin system identifier",
        examples=["claude-code", "manual", "codex-cli", "chatgpt"],
        max_length=100,
    )
    namespace: NamespaceStr = Field(
        ...,
        description="Project namespace for isolation",
        examples=["azure-msp", "default"],
    )
    source_id: str | None = Field(
        None, description="Original ID in the source system", max_length=255
    )
    source_event_id: str | None = Field(
        None,
        description="Connector-specific idempotency key",
        max_length=255,
    )
    occurred_at: datetime | None = Field(
        None, description="When the event happened (defaults to now)"
    )
    metadata: dict = Field(default_factory=dict, description="Additional context (freeform JSON)")
    participants: list[str] = Field(
        default_factory=list,
        description="People involved in the episode",
        max_length=settings.borg_max_episode_participants,
    )

    @field_validator("metadata")
    @classmethod
    def _validate_metadata_size(cls, value: dict) -> dict:
        metadata_bytes = len(
            json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        )
        if metadata_bytes > settings.borg_max_episode_metadata_bytes:
            raise ValueError(
                f"metadata must be <= {settings.borg_max_episode_metadata_bytes} bytes when serialized"
            )
        return value

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Decided to use pgAudit for SOX compliance on all Borg tables.",
                    "source": "claude-code",
                    "namespace": "azure-msp",
                    "metadata": {"session_id": "abc123"},
                }
            ]
        }
    }


class EpisodeResponse(BaseModel):
    """Response after ingesting an episode."""

    episode_id: UUID = Field(..., description="Unique ID of the episode")
    status: str = Field(..., description="Ingestion result", examples=["accepted", "duplicate"])


# ══════════════════════════════════════════════
# Think (Compilation)
# ══════════════════════════════════════════════


class ThinkRequest(BaseModel):
    """Compile task-specific context from the knowledge graph."""

    query: str = Field(
        ..., description="What you need context for", examples=["Debug APIM retry issue"]
    )
    namespace: NamespaceStr | None = Field(
        None, description="Project namespace (defaults to 'default')"
    )
    model: TargetModel | None = Field(None, description="Target LLM for output format selection")
    task_hint: TaskHint | None = Field(None, description="Override automatic intent classification")

    @field_validator("model", mode="before")
    @classmethod
    def _normalize_model(cls, value: Any) -> Any:
        return normalize_target_model(value)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What patterns do I follow when debugging auth issues?",
                    "namespace": "azure-msp",
                    "model": "claude",
                    "task_hint": "debug",
                }
            ]
        }
    }


class ThinkResponse(BaseModel):
    """Compiled context package returned by borg_think."""

    compiled_context: str = Field(
        ..., description="The compiled context (XML or JSON depending on model)"
    )
    format: str = Field(..., description="Output format used", examples=["structured", "compact"])
    tokens: int = Field(..., description="Estimated token count of compiled context")
    task_class: str = Field(
        ..., description="Classified task type", examples=["debug", "architecture"]
    )
    namespace: str = Field(..., description="Namespace the compilation ran against")
    candidates_found: int = Field(..., description="Total candidates retrieved before ranking")
    candidates_selected: int = Field(..., description="Candidates that made it into the context")
    latency_ms: int = Field(..., description="End-to-end compilation time in milliseconds")


# ══════════════════════════════════════════════
# Recall (Search)
# ══════════════════════════════════════════════


class RecallRequest(BaseModel):
    """Search raw memory without compilation."""

    query: str = Field(..., description="What to search for", examples=["APIM authentication"])
    namespace: NamespaceStr = Field(
        ..., description="Project namespace to search", examples=["azure-msp"]
    )
    memory_type: MemoryType | None = Field(None, description="Filter by memory type (omit for all)")
    time_after: datetime | None = Field(None, description="Only return results after this time")
    time_before: datetime | None = Field(None, description="Only return results before this time")
    limit: int = Field(10, description="Maximum results to return", ge=1, le=100)


class RecallResult(BaseModel):
    """A single search result from borg_recall."""

    id: UUID = Field(..., description="Unique ID of the memory item")
    type: str = Field(..., description="Memory type", examples=["episode", "fact", "procedure"])
    content: str = Field(..., description="Text content (truncated to 500 chars for episodes)")
    source: str | None = Field(None, description="Source system or evidence status")
    occurred_at: datetime | None = Field(None, description="When this memory was created/observed")
    relevance_score: float | None = Field(
        None, description="Vector similarity score (0-1) if available"
    )


class RecallResponse(BaseModel):
    """Search results from borg_recall."""

    results: list[RecallResult] = Field(..., description="Matching memory items")
    total: int = Field(..., description="Number of results returned")
    namespace: str = Field(..., description="Namespace that was searched")


class EpisodeDetailResponse(BaseModel):
    """Full stored episode body and metadata."""

    id: UUID = Field(..., description="Episode ID")
    source: str = Field(..., description="Origin system identifier")
    source_id: str | None = Field(None, description="Optional source thread/document identifier")
    source_event_id: str | None = Field(
        None, description="Optional source event/message identifier"
    )
    namespace: str = Field(..., description="Namespace the episode belongs to")
    content: str = Field(..., description="Full stored episode content")
    occurred_at: datetime | None = Field(None, description="When the episode originally occurred")
    ingested_at: datetime | None = Field(None, description="When the episode was stored in Borg")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Stored episode metadata")
    participants: list[str] = Field(
        default_factory=list, description="Participants attached to the episode"
    )
    processed: bool = Field(..., description="Whether offline extraction has processed the episode")


# ══════════════════════════════════════════════
# Namespace Config
# ══════════════════════════════════════════════


class NamespaceConfigCreate(BaseModel):
    """Create a new namespace with configurable token budgets."""

    namespace: NamespaceStr = Field(
        ...,
        description="Unique namespace identifier",
        examples=["azure-msp", "project-sentinel"],
    )
    hot_tier_budget: int = Field(
        500, description="Max tokens for always-injected hot-tier context", ge=0
    )
    warm_tier_budget: int = Field(
        3000, description="Max tokens for per-query warm-tier retrieval", ge=0
    )
    description: str | None = Field(None, description="Human-readable description")


class NamespaceConfigUpdate(BaseModel):
    """Update an existing namespace's budgets or description."""

    hot_tier_budget: int | None = Field(None, description="New hot-tier token budget", ge=0)
    warm_tier_budget: int | None = Field(None, description="New warm-tier token budget", ge=0)
    description: str | None = Field(None, description="New description")


class NamespaceConfigResponse(BaseModel):
    """A single namespace configuration."""

    namespace: str
    hot_tier_budget: int
    warm_tier_budget: int
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class NamespaceDetailResponse(BaseModel):
    """Namespace config with usage statistics."""

    namespace: str
    hot_tier_budget: int
    warm_tier_budget: int
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    stats: dict = Field(..., description="Counts of entities, facts, episodes, procedures")


class NamespaceListResponse(BaseModel):
    """List of all namespace configurations."""

    count: int
    namespaces: list[NamespaceConfigResponse]


# ══════════════════════════════════════════════
# Admin Response Models
# ══════════════════════════════════════════════


class HealthResponse(BaseModel):
    """Service health including worker and queue status."""

    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["borg"])
    version: str | None = Field(None, examples=["0.1.0"])
    worker: str | None = Field(None, examples=["running", "stopped"])
    queue: dict | None = Field(None, description="Episode processing queue stats")


class QueueEpisode(BaseModel):
    id: str
    source: str
    namespace: str
    ingested_at: str | None = None
    content_length: int


class QueueResponse(BaseModel):
    """Processing queue status."""

    queue_depth: int = Field(..., description="Number of unprocessed episodes")
    failed_count: int = Field(..., description="Episodes with extraction errors")
    episodes: list[QueueEpisode]


class EntityItem(BaseModel):
    id: str
    name: str
    type: str
    tier: str | None = None
    salience: float | None = None
    access_count: int | None = None
    last_accessed: str | None = None
    episode_count: int | None = None
    aliases: list[str] = Field(default_factory=list)


class EntityListResponse(BaseModel):
    """Entities in a namespace with serving state."""

    namespace: str
    count: int
    entities: list[EntityItem]


class FactItem(BaseModel):
    id: str
    subject: str
    predicate: str
    object: str
    status: str
    review_required: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    valid_from: str | None = None
    salience: float | None = None
    access_count: int | None = None
    last_accessed: str | None = None


class FactListResponse(BaseModel):
    """Current facts in a namespace with serving state."""

    namespace: str
    count: int
    facts: list[FactItem]


class ProcedureItem(BaseModel):
    id: str
    pattern: str
    category: str | None = None
    confidence: float
    observations: int
    status: str
    tier: str | None = None
    first_observed: str | None = None
    last_observed: str | None = None


class ProcedureListResponse(BaseModel):
    """Procedures in a namespace."""

    namespace: str
    count: int
    procedures: list[ProcedureItem]


class ConflictItem(BaseModel):
    id: str
    entity_name: str
    entity_type: str
    candidates: list | dict
    created_at: str | None = None


class ConflictListResponse(BaseModel):
    """Unresolved entity resolution conflicts."""

    namespace: str
    count: int
    conflicts: list[ConflictItem]


class PredicateItem(BaseModel):
    predicate: str
    category: str
    inverse: str | None = None
    usage_count: int


class PendingPredicate(BaseModel):
    predicate: str
    occurrences: int
    needs_review: bool


class PredicateListResponse(BaseModel):
    """Canonical predicates and pending custom candidates."""

    canonical: list[PredicateItem]
    pending_candidates: list[PendingPredicate]


class SnapshotResponse(BaseModel):
    """A hot-tier snapshot."""

    snapshot_at: str | None = None
    hot_entities: list = Field(default_factory=list)
    hot_facts: list = Field(default_factory=list)
    hot_procedures: list = Field(default_factory=list)
    total_tokens: int | None = None


class SnapshotTriggerResponse(BaseModel):
    """Result of manually triggering a snapshot."""

    status: str
    snapshots: list[dict]


# ══════════════════════════════════════════════
# Audit (internal, not exposed as response model)
# ══════════════════════════════════════════════


class ScoreBreakdown(BaseModel):
    relevance: float = 0.0
    recency: float = 0.0
    stability: float = 0.0
    provenance: float = 0.0
    composite: float = 0.0


class AuditEntry(BaseModel):
    task_class: str
    namespace: str
    query_text: str | None = None
    target_model: str | None = None
    retrieval_profile: str
    candidates_found: int = 0
    candidates_selected: int = 0
    candidates_rejected: int = 0
    selected_items: list[dict] = Field(default_factory=list)
    rejected_items: list[dict] = Field(default_factory=list)
    compiled_tokens: int = 0
    output_format: str = "structured"
    latency_total_ms: int = 0
    latency_classify_ms: int = 0
    latency_retrieve_ms: int = 0
    latency_rank_ms: int = 0
    latency_compile_ms: int = 0
