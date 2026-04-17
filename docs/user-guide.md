# Borg User Guide

Getting started with Borg as a daily tool for persistent AI context.

---

## Prerequisites

- Docker and Docker Compose
- An OpenAI API key (for entity/fact extraction)
- One or more AI tools: Claude Code, Codex CLI, Kiro, ChatGPT exports, or Copilot

Without an OpenAI API key, Borg still works — episodes are stored and searchable by recency, but no entities, facts, or procedures are extracted. Add credentials later and requeue.

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/villanub/borgmemory && cd borgmemory
cp .env.basic.example .env.basic
```

Edit `.env.basic` with your credentials:

```
OPENAI_API_KEY=sk-...
BORG_PUBLIC_BASE_URL=http://localhost:8080
```

### 2. Start the stack

```bash
docker compose -f docker-compose.basic.yml --env-file .env.basic up -d
```

This starts two containers:

- **borg-engine** — FastAPI server + background worker on port 8080
- **borg-db** — PostgreSQL 16 with pgvector on port 5433 (external) / 5432 (internal)

### 3. Verify

```bash
curl http://localhost:8080/health
```

You should see a liveness response like `{"status":"ok","profile":"basic"}`.

---

## Connecting your AI tools

### Codex CLI

```bash
# Add the server once in ~/.codex/config.toml:
[mcp_servers.borg]
url = "http://localhost:8080/mcp"
```

Start a fresh Codex session after saving that config.

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "borg": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

No auth header needed — Borg accepts all local connections.

### Claude Code and Kiro

Configure the MCP server in each client's settings. No auth required for local Borg.

Add this to your project's `CLAUDE.md` or `AGENTS.md`:

```markdown
## Borg Memory System
Call borg_think before complex tasks to retrieve professional context.
Call borg_learn after significant decisions or discoveries.
Call borg_recall when you want raw memory or direct evidence.
Use any namespace string that makes sense for your project.
```

For the Borg repository itself, use a project-specific override:

```markdown
## Borg Namespace

For this repository, use Borg namespace `borg`.

Always pass `namespace="borg"` to:
- `borg_think`
- `borg_learn`
- `borg_recall`

Do not omit the namespace.
Do not use `default` for work in this repository.
```

Optional auto-capture hook (records every session automatically):

```json
{
  "hooks": {
    "PostSession": [{
      "matcher": "",
      "command": "borg-capture.sh"
    }]
  }
}
```

### Manual ingestion (REST)

For pasting conversation exports, notes, or meeting summaries:

```bash
curl -X POST http://localhost:8080/api/learn \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Decided to use pgvector for embeddings. Rationale: single Postgres, no additional infrastructure, recursive CTEs handle graph traversal adequately for 1-2 hops.",
    "source": "manual",
    "namespace": "default"
  }'
```

---

## Namespaces

All memory is isolated by namespace. Use any namespace string you like — Borg has no namespace restrictions in local mode. Common patterns:

| Namespace | Purpose |
|-----------|---------|
| `default` | General knowledge not tied to a project |
| `<project-name>` | Scope memory to a single project |
| `personal` | Personal notes and decisions |

Use a global instruction file for broad namespace mapping across projects. Use a
project instruction file such as `CLAUDE.md` or `AGENTS.md` to pin the exact
namespace for a specific repository.

Create a new namespace:

```bash
curl -X POST http://localhost:8080/api/namespaces \
  -H "Content-Type: application/json" \
  -d '{"namespace": "project-alpha", "description": "Project Alpha notes"}'
```

Each namespace has configurable token budgets:

- **hot_tier_budget** (default 500) — always-injected context
- **warm_tier_budget** (default 3000) — per-query retrieval budget

---

## Daily usage

### How borg_think works

When your AI tool calls `borg_think("debug retry issue", namespace="default")`, the online pipeline:

1. Classifies the query as `debug` (with possible secondary class)
2. Runs 2-3 retrieval strategies: graph traversal, episode recall, fact lookup
3. Scores every candidate on relevance, recency, stability, and provenance
4. Trims to the namespace's token budget
5. Compiles into XML (for Claude/Copilot) or JSON (for GPT/Codex)
6. Returns the compiled context to your AI tool

Your AI tool receives structured context with the most relevant facts, recent episodes, and known procedures — without you having to re-explain anything.

### How borg_learn works

When you or your AI tool calls `borg_learn`, the episode is stored immediately (milliseconds). The background worker then asynchronously:

1. Generates a vector embedding for similarity search
2. Extracts entities (people, projects, services, technologies)
3. Resolves entities against the existing knowledge graph
4. Extracts facts as subject-predicate-object triples
5. Checks for superseded facts (contradictions update the old fact)
6. Extracts candidate procedures (repeatable patterns)

Check processing status anytime:

```bash
curl http://localhost:8080/api/admin/queue
```

### What to record

Good episodes include the **decision and the reasoning**, not just the outcome:

- "Decided to use pgvector instead of Qdrant. Reason: single database, no sync drift. Trade-off: may need dedicated vector DB at scale."
- "Fixed retry loop: root cause was XML escaping in service token. Solution: URL-encode before injecting into policy XML."
- "Convention: all resource groups use `{env}-{service}-rg` naming."

Avoid: secrets, credentials, PII, or content that's too vague to extract knowledge from.

### Browsing memory

Use `borg_recall` or the admin endpoints to see what Borg knows:

```bash
# What entities does Borg know about?
curl "http://localhost:8080/api/admin/entities?namespace=default"

# What facts are stored?
curl "http://localhost:8080/api/admin/facts?namespace=default"

# What procedures has Borg identified?
curl "http://localhost:8080/api/admin/procedures?namespace=default"

# Any entity resolution conflicts to review?
curl "http://localhost:8080/api/admin/conflicts?namespace=default"

# Fetch one full episode after getting its id from borg_recall
curl "http://localhost:8080/api/episodes/11111111-1111-1111-1111-111111111111"
```

---

## Seeding from existing conversations

Bootstrap scripts can ingest conversation exports from your AI tools:

```bash
# Place export files in ./exports/
python -m bootstrap.loader default
```

Supported formats: Claude.ai exports, Claude Code session logs, Codex CLI history, ChatGPT export JSON.

After seeding, monitor the worker:

```bash
# Watch queue drain
watch -n 5 'curl -s http://localhost:8080/api/admin/queue | python -m json.tool'
```

---

## API documentation

Interactive Swagger docs are available when the engine is running:

- **Live docs**: http://localhost:8080/docs (when `BORG_ENABLE_DOCS=true`)
- **OpenAPI spec**: http://localhost:8080/openapi.json (when `BORG_ENABLE_DOCS=true`)

All endpoints are open in local mode — no auth header required.

---

## Monitoring and troubleshooting

### Health check

```bash
curl http://localhost:8080/health
```

Returns a liveness payload including worker and queue metrics.

### Processing queue

```bash
curl http://localhost:8080/api/admin/queue
```

Shows unprocessed episodes and count of failed extractions.

### Failed extractions

Episodes that fail extraction are marked with `extraction_error` in metadata and won't retry automatically. To requeue after fixing the issue (e.g., adding an OpenAI API key):

```bash
curl -X POST "http://localhost:8080/api/admin/requeue-failed?namespace=default"
```

### Manual extraction

Trigger extraction for a specific episode:

```bash
curl -X POST "http://localhost:8080/api/admin/process-episode?episode_id=YOUR-UUID"
```

### Predicate review

Non-canonical predicates extracted by the LLM are tracked. Those with 5+ occurrences are flagged for promotion:

```bash
curl http://localhost:8080/api/admin/predicates
```

### Snapshots

Hot-tier snapshots are written every 24 hours automatically. To trigger manually or view the latest:

```bash
# Trigger snapshot
curl -X POST http://localhost:8080/api/admin/snapshot

# View latest
curl "http://localhost:8080/api/admin/snapshot/latest?namespace=default"
```

### Container logs

```bash
docker compose -f docker-compose.basic.yml logs -f borg-engine
```

Look for `worker.batch_complete`, `extraction.complete`, and `snapshot.written` entries to confirm the offline pipeline is running.

### Common issues

**Episodes stuck in queue**: Check that `OPENAI_API_KEY` is set in `.env.basic` and the container was restarted after changes. The worker logs `extraction.skipped` with reason `OpenAI not configured` if credentials are missing.

**Entity resolution conflicts**: Check `/api/admin/conflicts`. Borg deliberately fragments ambiguous entities rather than risk incorrect merges. Review conflicts and merge manually via SQL if appropriate.

**Empty borg_think results**: The namespace may not have relevant data yet, or the query keywords don't match entity names. Try `borg_recall` to see what's available, or check if episodes have been processed via `/api/admin/queue`.

**High latency on borg_think**: Check the audit log for per-stage latency breakdown. Retrieval is typically the bottleneck — ensure pgvector indexes exist and episode embeddings are populated.

---

## Running benchmarks

Borg includes an automated benchmark harness that tests retrieval quality across 10 benchmark scenarios modeled on real work patterns.

### Seed test data

```bash
source .venv/bin/activate
python -m bench.seed
```

This loads 20 synthetic episodes and waits for the extraction pipeline to process them into entities, facts, and procedures.

### Run the benchmark

```bash
python -m bench.runner              # Full run: 10 tasks × 3 conditions
python -m bench.runner --task task-01  # Single task
python -m bench.runner --condition C   # Single condition
python -m bench.runner --dry-run       # Preview plan
python -m bench.runner --report        # Report from existing results
```

Results are written to `bench/results/` including per-task JSON scores, a markdown report with decision gate analysis, and a detailed log file.

### Interpreting results

The benchmark compares three conditions: A (no memory), B (top-10 vector episodes as raw text), and C (full Borg compilation). The decision gate checks whether C beats B on precision (≥15%), tokens (≥30% reduction), and task success (no regression).
