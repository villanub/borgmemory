# Borg — The PostgreSQL-native memory compiler for AI coding agents.

Run one install command, type `borg init` in your project, and every AI coding session builds a knowledge graph that makes the next session smarter — one Postgres, no SDKs, no Neo4j.

---

## Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/villanub/borgmemory/main/install.sh | sh
```

```bash
borg init
```

That's it. The installer detects Docker, sets up the stack with your OpenAI API key, and starts the engine. `borg init` detects which AI tools you use (Claude Code, Copilot, Codex, Kiro) and writes the right project settings file so your agent starts recording and retrieving automatically.

---

## What It Does

**1. Learns automatically via CLAUDE.md.**
Drop one line in your project's CLAUDE.md and your AI coding agent calls `borg_learn` after significant decisions and discoveries. No SDK import. No wrapper code. Borg rides the existing tool's hook system.

**2. Extracts structure.**
In the background, Borg processes each episode: generates embeddings, extracts entities and facts via LLM, resolves them against the existing graph, and tracks which facts supersede earlier ones. Stale decisions don't contaminate future answers.

**3. Compiles context.**
When your agent calls `borg_think`, Borg classifies the query intent, selects retrieval profiles, ranks candidates across four dimensions (relevance, recency, stability, provenance), and delivers a formatted context package. Not raw search results — compiled ranked context.

---

## Why Not Mem0 / Zep / Cognee?

| | Mem0 | Zep | Cognee | Borg |
|---|---|---|---|---|
| Databases required | 2 (Qdrant + Neo4j) | 2 (Neo4j + vectors) | 3+ | 1 (Postgres) |
| Integration | Python SDK | Python SDK | Python SDK | One line in CLAUDE.md |
| Retrieval | Raw results | Raw results | Raw results | Compiled ranked context |
| Stale facts | No tracking | Temporal (Neo4j) | No tracking | Temporal validity (`valid_until`) |

Every competitor returns raw search results and requires 2-3 databases. Borg is a single Postgres with pgvector and recursive CTEs, and it compiles context rather than dumping matches.

---

## Benchmark Results

10 tasks modeled on real engineering work patterns. Three conditions: A (no memory), B (simple top-10 vector retrieval), C (full Borg compilation).

| Condition | Task Success | Retrieval Precision | Stale Fact Rate |
|---|---|---|---|
| A — No Memory | 0 / 10 | 0.060 | 0.000 |
| B — Simple RAG | 8 / 10 | 0.810 | 0.115 |
| C — Borg Compiled | 10 / 10 | 0.913 | 0.025 |

Borg compiled context solved every task, raised precision by 12.7 points over vector RAG, and cut the stale fact rate by 78%.

---

## How It Works

```
Developer works in Claude Code / Copilot / Codex / Kiro
        |
        | CLAUDE.md triggers borg_learn automatically
        v
 borg-engine receives episode
        |
        | Background worker
        | - Embed + extract entities and facts via LLM
        | - Resolve against existing knowledge graph
        | - Supersede contradicting facts (valid_until = now)
        v
 PostgreSQL knowledge graph
 (episodes, entities, facts, predicates)
        |
        | Next session: borg_think called before complex task
        v
 Compiler pipeline
 - Classify intent
 - Select retrieval profiles (vector + graph + recency)
 - Rank by relevance x recency x stability x provenance
 - Format for target model
        |
        v
 Compiled context injected into assistant prompt
        |
        v
 Better answers on the first attempt
```

---

## License

Borg is open source under the Apache 2.0 license. Single-user, local, no auth — run it on your workstation or a VM you control.

---

## Documentation

- [Getting Started](docs/getting-started.md) — Local single-user setup in 3 commands
- [Architecture](docs/borg-v2-1-current.md) — Engine design, compiler pipeline, offline worker
- [Benchmark Details](bench/results/report.md) — Full per-task results and evaluation reasoning

---

## License

Apache 2.0. See `LICENSE` for details.

---

## Disclaimer

This is an independent open-source project. It is not affiliated with, endorsed by, or connected to any company, brand, franchise, or intellectual property referenced — directly or indirectly — by the project name or any term used in this repository, including (but not limited to) Paramount Global, CBS Studios, the Star Trek franchise, Anthropic, OpenAI, Microsoft, GitHub, or any other third party. All product names, trademarks, and registered trademarks are property of their respective owners.
