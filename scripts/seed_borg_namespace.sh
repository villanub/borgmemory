#!/bin/bash
# Bootstrap Borg's own knowledge into the borg namespace.
# Run: bash scripts/seed_borg_namespace.sh

set -euo pipefail

API="${BORG_PUBLIC_BASE_URL:-http://localhost:8080}/api/learn"
CT="Content-Type: application/json"

echo "=== Seeding borg namespace ==="

curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Project Borg is an Apache-2.0, PostgreSQL-native memory compiler for local AI workflows. It records important project events through MCP tools, extracts entities, facts, and procedures into a temporal knowledge graph, and compiles task-specific context packages for future assistant sessions. The public release is single-user, local-first, and runs without auth.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg architecture centers on two separated pipelines sharing PostgreSQL. The online pipeline serves borg_think by classifying intent, retrieving candidates, ranking them, compiling context, updating access tracking, and writing an audit trace. The offline pipeline processes borg_learn episodes by storing the episode, generating embeddings, extracting entities and facts, resolving graph records, extracting procedures, and periodically capturing hot-tier snapshots.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg technology stack: FastAPI and Python 3.12 serve REST and MCP on port 8080. PostgreSQL with pgvector stores relational data, vector embeddings, graph edges, and audit records. Docker Compose runs a local borg-engine service and a pgvector database. OpenAI is used for embeddings and extraction when configured; without credentials, Borg still stores raw episodes for later processing.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg exposes MCP tools for memory work. borg_think compiles task-specific context from the knowledge graph. borg_learn records decisions, discoveries, and conversations for future reference. borg_recall searches memory directly without compilation. borg_get_episode fetches a complete stored episode after recall identifies it. The OSS release accepts local MCP connections without login.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg REST API surface mirrors the core memory operations: POST /api/think, POST /api/learn, and POST /api/recall. Namespace endpoints manage local namespace configuration. Admin endpoints expose local inspection and maintenance actions for queues, entities, facts, procedures, conflicts, predicates, snapshots, and cost summaries. Swagger docs are available at /docs when enabled.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg uses hard namespace isolation. Every episode, entity, fact, and procedure belongs to one namespace. Retrieval is scoped to the requested namespace, so similarly named entities in different projects remain separate. The default namespace is available for general memory, while project-specific namespaces keep work context tidy.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Key Borg design decisions: use one PostgreSQL database for relational, vector, graph, and audit data; run LLM extraction offline so query latency stays predictable; prefer entity fragmentation over incorrect merges; use task-specific memory weights instead of one universal ranking; and keep superseded facts as history rather than deleting them.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

curl -s -X POST "$API" -H "$CT" -d '{
  "content": "Borg project structure: source code lives under src/borg. main.py creates the FastAPI app and worker lifecycle, config.py reads environment variables, db/ manages asyncpg connections and migrations, api/ exposes REST routes, mcp/ exposes MCP tools, compiler/ handles online retrieval and formatting, extraction/ handles offline structure extraction, and ingestion/ stores deduplicated episodes.",
  "source": "manual",
  "namespace": "borg"
}' && echo ""

echo ""
echo "=== Done. Check processing queue: ==="
echo "curl ${BORG_PUBLIC_BASE_URL:-http://localhost:8080}/api/admin/queue"
