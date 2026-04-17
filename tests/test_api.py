"""Targeted tests for request validation and MCP tool entrypoints."""

import json

import pytest
from fastmcp.server.auth import AccessToken

import borg.compiler
import borg.db as db_module
from borg.compiler.classify import ClassificationResult
from borg.config import settings
from borg.mcp import borg_get_episode, borg_think
from borg.models import TargetModel, ThinkRequest, ThinkResponse


@pytest.mark.parametrize(
    ("raw_model", "expected"),
    [
        ("gpt-5.2", TargetModel.gpt),
        ("gpt-4.1-mini", TargetModel.gpt),
        ("codex-mini-latest", TargetModel.gpt),
        ("claude-3-7-sonnet", TargetModel.claude),
        ("github-copilot", TargetModel.copilot),
        ("llama3.3", TargetModel.local),
    ],
)
def test_think_request_normalizes_model_aliases(raw_model, expected):
    request = ThinkRequest(query="Check Borg", namespace="borg", model=raw_model)

    assert request.model is expected


@pytest.mark.asyncio
async def test_borg_think_accepts_specific_model_names(monkeypatch):
    seen = {}

    async def fake_compile_context(req):
        seen["req"] = req
        return (
            ThinkResponse(
                compiled_context='{"status":"ok"}',
                format="compact",
                tokens=3,
                task_class="chat",
                namespace="borg",
                candidates_found=0,
                candidates_selected=0,
                latency_ms=1,
            ),
            None,
        )

    monkeypatch.setattr(borg.compiler, "compile_context", fake_compile_context)

    token = AccessToken(
        token="token",
        client_id="client-id",
        scopes=["access_as_user"],
        claims={settings.entra_namespace_claim: ["borg"]},
    )

    result = await borg_think(
        query="Check Borg",
        namespace="borg",
        model="gpt-5.2",
        task_hint="chat",
        token=token,
    )

    assert result == '{"status":"ok"}'
    assert seen["req"].model is TargetModel.gpt


@pytest.mark.asyncio
async def test_compile_context_minimizes_audit_payloads(monkeypatch):
    captured = {}

    async def fake_classify_intent(_query, _task_hint):
        return ClassificationResult(
            primary_class="architecture",
            secondary_class=None,
            primary_confidence=1.0,
            secondary_confidence=None,
            retrieval_profiles=["fact_lookup"],
            memory_weights=(0.5, 1.0, 0.3),
        )

    async def fake_retrieve_candidates(**_kwargs):
        return [{"type": "fact", "id": "11111111-1111-1111-1111-111111111111", "content": "raw"}]

    async def fake_rank_and_trim(*_args, **_kwargs):
        selected = [
            {
                "type": "fact",
                "id": "11111111-1111-1111-1111-111111111111",
                "content": "Borg uses Entra",
                "audit": {
                    "type": "fact",
                    "id": "11111111-1111-1111-1111-111111111111",
                    "predicate": "uses",
                    "from_entity": "Borg",
                    "to_entity": "Entra",
                    "score_breakdown": {
                        "relevance": 0.8,
                        "composite": 0.9,
                        "memory_type": "semantic",
                    },
                },
            }
        ]
        rejected = [
            {
                "type": "episode",
                "id": "22222222-2222-2222-2222-222222222222",
                "content": "Older note",
                "audit": {
                    "type": "episode",
                    "id": "22222222-2222-2222-2222-222222222222",
                    "source": "claude-code",
                    "occurred_at": "2026-03-18T00:00:00+00:00",
                    "rejection_reason": "budget_exceeded",
                    "score_breakdown": {
                        "recency": 0.6,
                        "composite": 0.3,
                        "memory_type": "episodic",
                    },
                },
            }
        ]
        return selected, rejected

    async def fake_compile_package(**_kwargs):
        return '{"status":"ok"}', 3

    async def fake_update_access_tracking(_selected):
        return None

    class FakeConn:
        async def fetchrow(self, _query, _namespace):
            return None

        async def execute(self, query, *args):
            if "INSERT INTO borg_audit_log" in query:
                captured["query_text"] = args[2]
                captured["selected_items"] = json.loads(args[8])
                captured["rejected_items"] = json.loads(args[9])

    class FakeConnContext:
        async def __aenter__(self):
            return FakeConn()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(borg.compiler, "classify_intent", fake_classify_intent)
    monkeypatch.setattr(borg.compiler, "retrieve_candidates", fake_retrieve_candidates)
    monkeypatch.setattr(borg.compiler, "rank_and_trim", fake_rank_and_trim)
    monkeypatch.setattr(borg.compiler, "compile_package", fake_compile_package)
    monkeypatch.setattr(borg.compiler, "_update_access_tracking", fake_update_access_tracking)
    monkeypatch.setattr(borg.compiler, "get_conn", lambda: FakeConnContext())

    response, audit = await borg.compiler.compile_context(
        ThinkRequest(query="What is Borg doing with Entra auth?", namespace="borg", model="gpt-5.2")
    )

    assert response.compiled_context == '{"status":"ok"}'
    assert audit.query_text.startswith("sha256:")
    assert "What is Borg doing" not in audit.query_text
    assert captured["query_text"] == audit.query_text
    assert captured["selected_items"] == [
        {
            "type": "fact",
            "id": "11111111-1111-1111-1111-111111111111",
            "score_breakdown": {"relevance": 0.8, "composite": 0.9},
        },
        {
            "type": "episode",
            "id": "22222222-2222-2222-2222-222222222222",
            "score_breakdown": {"recency": 0.6, "composite": 0.3},
            "rejection_reason": "hybrid_reinstated",
        },
    ]
    assert captured["rejected_items"] == [
        {
            "type": "episode",
            "id": "22222222-2222-2222-2222-222222222222",
            "score_breakdown": {"recency": 0.6, "composite": 0.3},
            "rejection_reason": "hybrid_reinstated",
        }
    ]


@pytest.mark.asyncio
async def test_borg_get_episode_returns_full_content(monkeypatch):
    episode_id = "11111111-1111-1111-1111-111111111111"

    class FakeConn:
        async def fetchrow(self, query, lookup_id):
            assert "FROM borg_episodes" in query
            assert str(lookup_id) == episode_id
            return {
                "id": lookup_id,
                "source": "codex-cli",
                "source_id": None,
                "source_event_id": None,
                "namespace": "borg",
                "content": "Full episode body for MCP retrieval.",
                "occurred_at": None,
                "ingested_at": None,
                "metadata": {},
                "participants": ["ben", "borg"],
                "processed": True,
            }

    class FakeConnContext:
        async def __aenter__(self):
            return FakeConn()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(db_module, "get_conn", lambda: FakeConnContext())

    token = AccessToken(
        token="token",
        client_id="client-id",
        scopes=["access_as_user"],
        claims={settings.entra_namespace_claim: ["borg"]},
    )

    result = await borg_get_episode(episode_id=episode_id, token=token)

    assert "## Episode" in result
    assert f"- id: {episode_id}" in result
    assert "### Content" in result
    assert "Full episode body for MCP retrieval." in result
