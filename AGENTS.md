# AGENTS.md — Project Borg

## What is Borg?

Borg is a memory system connected via MCP. It maintains a knowledge graph of entities, facts, and procedures extracted from past conversations across all your AI tools. Use it to avoid re-explaining context and to make decisions informed by prior work.

## When to use Borg

### borg_think — Call BEFORE starting complex tasks

Call `borg_think` before any task that would benefit from knowing what was done previously. This compiles relevant context from the knowledge graph and returns it as structured output.

**Always call borg_think when:**
- Starting work on any file or module you haven't seen in this session
- Debugging an issue (retrieves past bugs, patterns, and related decisions)
- Making an architecture or design decision (retrieves prior decisions and rationale)
- Writing documentation, proposals, or RFPs (retrieves relevant facts and terminology)
- Asked about project history, prior decisions, or "what did we decide about X"
- Working in a namespace/project area you haven't touched recently

**Example calls:**
```
borg_think(query="APIM authentication issues", namespace="azure-msp", task_hint="debug")
borg_think(query="AMA compliance tracking architecture", namespace="azure-msp", task_hint="architecture")
borg_think(query="Project Sentinel customer targeting", namespace="azure-msp", task_hint="writing")
```

**Task hints** (use the most specific one):
- `debug` — retrieves episodic memory + procedures + graph traversal
- `architecture` — retrieves semantic facts + graph neighborhood
- `compliance` — retrieves episode evidence + facts, excludes procedures
- `writing` — retrieves semantic facts for accurate terminology
- `chat` — lightweight fact lookup (default)

### borg_learn — Call AFTER significant events

Call `borg_learn` to record decisions, discoveries, and important context that should persist across sessions. The background worker extracts entities, facts, and procedures automatically.

**Always call borg_learn when:**
- A significant decision is made (technology choice, architecture change, policy)
- A non-obvious bug is diagnosed and fixed (root cause + solution)
- A new pattern or convention is established
- Important context is shared that would be lost when this session ends
- A meeting outcome, customer conversation, or requirement is discussed

**Example calls:**
```
borg_learn(
  content="Decided to use pgvector instead of Qdrant for embeddings. Reason: single database, no sync drift, ACID compliance. Trade-off: may need dedicated vector DB at scale.",
  source="codex-cli",
  namespace="borg"
)

borg_learn(
  content="Fixed APIM retry loop: root cause was XML escaping in service token. Solution: URL-encode the token before injecting into policy XML.",
  source="codex-cli",
  namespace="azure-msp"
)
```

**What makes a good episode:**
- Include the decision AND the reasoning (not just "we chose X" but "we chose X because Y, trading off Z")
- Include the problem AND the solution for bugs
- Be specific — entity names, service names, file paths help extraction
- One topic per episode — don't combine unrelated decisions

### borg_recall — Call for direct memory search

Call `borg_recall` when you need to search memory without the compilation overhead. Returns raw results.

**Use borg_recall when:**
- Looking for a specific past conversation or decision
- Checking if something was already recorded
- Browsing what Borg knows about a topic

```
borg_recall(query="APIM", namespace="azure-msp", memory_type="semantic")
borg_recall(query="retry", namespace="azure-msp", memory_type="episodic")
```

## Namespaces

All memory is namespace-isolated. Always use the correct namespace:
- `azure-msp` — Rackspace Azure Expert MSP platform work
- `borg` — Project Borg development itself
- `default` — General knowledge not tied to a specific project

When unsure, use `default`.

## Important

- Borg's memory persists across sessions and across AI tools. What you record here is available in Claude Code, ChatGPT, and other connected clients.
- Do not store secrets, credentials, or PII in borg_learn calls.
- Borg extracts entities and facts automatically — you don't need to structure the content, just write naturally.
- If borg_think returns empty context, that's fine — the namespace may not have relevant data yet. Proceed normally.
