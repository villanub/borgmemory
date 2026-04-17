#!/bin/bash
# Bootstrap Borg's own knowledge into the borg namespace.
# Run: bash scripts/seed_borg_namespace.sh

set -euo pipefail

API="http://localhost:8080/api/learn"
CT="Content-Type: application/json"

echo "=== Seeding borg namespace ==="

# 1. Project Overview
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Project Borg is a PostgreSQL-native memory compiler for AI workflows. It watches work across AI tools (Claude Code, Codex CLI, ChatGPT, Claude Desktop), extracts entities, facts, and procedures into a temporal knowledge graph, and compiles task-specific context packages for any LLM. The central principle: keep the architecture narrow, prove retrieval quality before adding memory sophistication. One PostgreSQL database, every client. No context lost between sessions. Built by Benjamin Molinet, Cloud Architect and AI Modernization Lead at Rackspace Technology on the Azure Expert MSP team.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 2. Architecture — Two Pipelines
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg architecture centers on two strictly separated pipelines sharing a database but never sharing runtime. The Online Pipeline (7 stages) serves borg_think queries and is latency-sensitive: 1) dual-profile intent classification, 2) namespace resolution, 3) candidate retrieval from up to 3 strategies, 4) rank and trim with 4-dimension scoring and memory-type weight modifiers, 5) compile package (structured XML for Claude/Copilot, compact JSON for GPT/Codex), 6) update access tracking on entity_state and fact_state, 7) audit log with full trace. The Offline Pipeline (10 steps) processes episodes via borg_learn asynchronously: 1) ingest + dedup, 2) generate embedding, 3) extract entities, 4) three-pass entity resolution, 5) extract facts + validate predicates, 6) supersession check, 7) extract procedures, 8) create serving state, 9) mark processed, 10) periodic 24h hot-tier snapshots.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 3. Technology Stack
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg technology stack: Runtime is FastAPI + Python 3.12 serving MCP + REST on port 8080. Database is PostgreSQL 14+ with pgvector for embeddings, recursive CTEs for graph traversal, and pgAudit for SOX compliance (available on Azure PostgreSQL, not in Docker image). Extraction uses Azure OpenAI gpt-5-mini for entity, fact, and procedure extraction plus text-embedding-3-small for 1536-dim embeddings. Deployment target is Azure Container Apps at estimated cost of 50-90 dollars per month. Docker Compose for local development with pgvector/pgvector:pg16 image. The MCP server uses FastMCP 3 with Streamable HTTP transport and Entra-backed OAuth discovery.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 4. Schema — 15 Tables
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg database schema consists of 15 tables plus 1 function, all prefixed with borg_. Canonical tables: borg_episodes (immutable evidence layer with SHA-256 dedup), borg_entities (graph nodes with typed taxonomy and aliases), borg_facts (temporal graph edges with valid_from/valid_until and supersession), borg_procedures (candidate behavioral patterns with confidence scoring and observation counts), borg_predicates (24 canonical relationship predicates across structural/temporal/decisional/operational categories), borg_predicate_candidates (non-canonical predicates pending review). Derived tables: borg_entity_state (tier, salience, access_count, last_accessed), borg_fact_state (salience, access_count for ranking). Infrastructure tables: borg_audit_log (full compilation + extraction traces with dual-profile fields), borg_snapshots (24h hot-tier state captures), borg_namespace_config (per-namespace token budgets), borg_resolution_conflicts (ambiguous entity matches). Function: borg_traverse() for 1-2 hop cycle-safe recursive CTE graph traversal.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 5. Three MCP Tools
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg exposes exactly three MCP tools via Streamable HTTP transport. borg_think compiles task-specific context from the knowledge graph — runs the full online pipeline (classify, retrieve, rank, compile, audit). Parameters: query (required), namespace, model (claude/gpt/local/copilot), task_hint (debug/architecture/compliance/writing/chat). borg_learn records decisions, discoveries, and conversations for future reference — stores immediately, extraction happens in background. Parameters: content (required), source (required), namespace (required), metadata. borg_recall searches memory directly without compilation — returns raw episodes, facts, and procedures. Parameters: query (required), namespace (required), memory_type (semantic/episodic/procedural). Connected to Claude Code, Codex CLI, and Claude Desktop via MCP.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 6. Entity Resolution
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg uses a three-pass entity resolution algorithm with the design principle: prefer fragmentation over collision. Two separate entities for the same thing can be merged later with a simple UPDATE; two different things incorrectly merged corrupt every fact attached to both. Pass 1: exact match on LOWER(name) + entity_type + namespace, confidence 1.0. Pass 2: alias match on properties->aliases array, confidence 0.95, single match only. Pass 3: semantic similarity via entity_state embedding with threshold 0.92; if top two candidates are within 0.03 gap, flag as ambiguous in borg_resolution_conflicts and create new entity. Entity types: person, organization, project, service, technology, pattern, environment, document, metric, decision.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 7. Predicate Registry
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg maintains a canonical predicate registry of 24 predicates across four categories. Structural: uses/used_by, contains/contained_in, depends_on/dependency_of, implements/implemented_by, integrates_with, authored/authored_by, owns/owned_by. Temporal: replaced/replaced_by. Decisional: decided/decided_by. Operational: deployed_to/hosts, manages/managed_by, configured_with, targets, blocked_by/blocks. Non-canonical predicates extracted by the LLM are flagged as custom and tracked in borg_predicate_candidates with occurrence counts. Once a candidate reaches 5 or more occurrences, it is surfaced as needs_review in the admin API.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 8. Ranking and Compilation
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg ranks candidates on four interpretable dimensions with no opaque composite. Relevance (weight 0.40): vector similarity when available, multiplied by memory-type weight modifier. Recency (weight 0.25): linear decay over 90 days from occurred_at. Stability (weight 0.20): evidence status score blended with fact_state.salience_score at 70/30 ratio. Provenance (weight 0.15): retrieval source quality (procedure_assist=0.9, fact_lookup=0.8, graph_neighborhood=0.7, episode_recall=0.6). Memory-type weight modifiers per task class bias ranking without hard exclusion: debug (1.0, 0.7, 0.8), architecture (0.5, 1.0, 0.3), compliance (1.0, 0.8, 0.0 — procedural excluded), writing (0.3, 1.0, 0.6), chat (0.4, 1.0, 0.3). Output formats: structured XML for Claude/Copilot, compact JSON for GPT/Codex.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 9. Namespace Isolation
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg enforces hard namespace isolation by default. Every entity, fact, episode, and procedure belongs to exactly one namespace. All queries are scoped to one namespace with no cross-namespace retrieval. If the same real-world entity like APIM appears in two projects, it exists as two separate entity records. Hot-tier content is namespace-scoped with no global hot tier. Namespaces are managed via full CRUD REST endpoints at /api/namespaces with configurable hot_tier_budget (default 500 tokens) and warm_tier_budget (default 3000 tokens). The default namespace is seeded automatically and cannot be deleted. Active namespaces include: borg (this project), azure-msp (Rackspace Azure platform work), default (general knowledge).",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 10. REST API Surface
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg REST API surface: Core endpoints — POST /api/think (compile context), POST /api/learn (ingest episode), POST /api/recall (search memory). Namespace management — GET/POST/PUT/DELETE /api/namespaces. Admin endpoints — GET /api/admin/queue (processing queue), GET /api/admin/entities (list entities with state), GET /api/admin/facts (list facts with salience), GET /api/admin/procedures (list procedures), GET /api/admin/conflicts (entity resolution conflicts), GET /api/admin/predicates (canonical + pending), POST /api/admin/process-episode (manual extraction), POST /api/admin/requeue-failed (requeue errors), POST /api/admin/snapshot (trigger snapshot), GET /api/admin/snapshot/latest. Health at GET /health. Swagger docs at /docs, ReDoc at /redoc, OpenAPI schema at /openapi.json. All endpoints except /health and /docs require Authorization Bearer token.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 11. Key Design Decisions
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Key design decisions in Project Borg: 1) PostgreSQL maximalism — one database for everything (relational, vector via pgvector, graph via recursive CTEs, audit via pgAudit). No Neo4j, no Qdrant, no separate vector store. Trade-off: may need escape hatch at scale. 2) LLM in the write path — required for structured entity/fact/procedure extraction, runs offline so never blocks queries. 3) Three-pass entity resolution preferring fragmentation over collision — 0.92 semantic threshold is deliberately high, ambiguous matches flagged for human review. 4) Task-specific memory weights instead of one ranking — different tasks need fundamentally different memory types. 5) Two output formats — structured XML for Claude (metadata attributes), compact JSON for GPT (minimal overhead). 6) Temporal facts with supersession — old facts marked superseded, never deleted, full history always available for compliance. 7) Four amendments incorporated: canonical predicate registry, entity resolution conflict tracking, dual-profile classification with memory weight modifiers, configurable namespace budgets.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 12. Project Structure
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg project structure at /Users/benj8956/Documents/Borg/. Source under src/borg/ with modules: main.py (FastAPI app + worker lifecycle), config.py (pydantic-settings from env), worker.py (background extraction loop + snapshot loop), snapshots.py (24h hot-tier capture), db/__init__.py (asyncpg pool + migration runner), models/__init__.py (Pydantic request/response models with OpenAPI metadata), api/__init__.py (REST routes with Swagger tags), mcp/__init__.py (FastMCP server with 3 tools), compiler/ (classify.py, retrieve.py, rank.py, format.py), extraction/ (pipeline.py, prompts.py, resolve.py, embed.py), ingestion/__init__.py (episode dedup + storage). Migrations under migrations/ (001_initial_schema.sql, 002_amendments.sql — both idempotent, run on every startup). Site under site/ (Next.js 15 + React 19 + Tailwind v4 project site). Docker setup: Dockerfile (python:3.12-slim), docker-compose.yml (borg-engine + borg-db with pgvector/pgvector:pg16).",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 13. Evaluation Plan
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg benchmark results published March 17 2026 cover 10 tasks across debug, architecture, compliance, writing, and procedure work. Three conditions were tested: A (no memory baseline), B (simple top-10 vector retrieval), and C (full Borg compilation pipeline). Current headline metrics: task success A 2/10, B 8/10, C 7/10; retrieval precision A 0.24, B 0.67, C 0.70; irrelevant rate A 25%, B 18%, C 16%; average context tokens A 0, B 1265, C 492. Conclusion: Borg currently improves precision and token efficiency, but does not yet beat simple retrieval on raw task success.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

# 14. Current Integrations
curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg is currently connected to three MCP clients. Codex CLI uses ~/.codex/config.toml with url http://localhost:8080/mcp and interactive login via codex mcp login borg. Claude Code and Kiro connect through npx mcp-remote http://localhost:8080/mcp so they can complete the same browser-based OAuth flow. All three clients share the same PostgreSQL database and see the same knowledge graph. The AGENTS.md file in the Borg project directory instructs Codex to call borg_think before complex tasks and borg_learn after significant decisions. Bootstrap scripts exist for seeding from Claude.ai, Claude Code, Codex CLI, and ChatGPT conversation exports.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

echo ""
echo "=== Done. Check processing queue: ==="
echo "curl http://localhost:8080/api/admin/queue"
