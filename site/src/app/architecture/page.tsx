import { Section } from "@/components/Section";

export default function Architecture() {
  return (
    <div className="pt-16">
      {/* Header */}
      <div className="border-b border-[var(--border)] bg-gradient-to-b from-[var(--accent-blue)]/5 to-transparent">
        <div className="mx-auto max-w-6xl px-6 pb-12 pt-20">
          <h1 className="text-4xl font-extrabold text-[var(--text-primary)]">
            Architecture
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-[var(--text-secondary)]">
            System design, schema, deployment, and the decisions behind them.
          </p>
          <p className="mt-2 text-sm text-[var(--text-muted)]">10 min read</p>
        </div>
      </div>

      {/* System Overview */}
      <Section
        id="overview"
        title="System Overview"
        subtitle="One container, one database, two pipelines. Runs locally against any Postgres 14+ instance."
      >
        <div className="space-y-6">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Reference Layout
            </h3>
            <pre className="!border-0 !bg-transparent !p-0 text-sm leading-7">
              <code>{`Local machine (or any container host)
├── borg-engine
│   ├── FastAPI (main.py)
│   ├── MCP endpoint (:8080/mcp)          ← Claude Code, Codex CLI, Kiro, Copilot
│   ├── REST endpoint (:8080/api)          ← Manual ingestion, admin
│   ├── Background worker                  ← Async extraction loop
│   └── Snapshot loop                      ← 24h hot-tier snapshots
│
├── PostgreSQL 14+ (local, Supabase, Neon, Azure, etc.)
│   ├── pgvector, pgAudit, uuid-ossp
│   └── borg_* tables (15 tables + 1 function)
│
└── OpenAI / Azure OpenAI
    ├── text-embedding-3-small             ← Episode embeddings (1536-dim)
    └── gpt-5-mini / gpt-4o-mini           ← Entity, fact, procedure extraction`}</code>
            </pre>
            <p className="mt-4 text-sm text-[var(--text-muted)]">
              Supports both standard OpenAI and Azure OpenAI endpoints. The engine
              runs as a single process with the API server and background worker
              as async tasks. Any Postgres 14+ instance with pgvector works.
            </p>
          </div>
        </div>
      </Section>

      {/* Schema */}
      <Section
        id="schema"
        title="Schema"
        subtitle="15 tables + 1 function. Every table separates canonical data from derived serving state."
        className="border-t border-[var(--border)]"
      >
        <div className="space-y-6">
          <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Table</th>
                  <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Role</th>
                  <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Type</th>
                  <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">Status</th>
                </tr>
              </thead>
              <tbody className="text-[var(--text-secondary)]">
                {[
                  ["borg_episodes", "Immutable evidence layer", "Canonical", "✅"],
                  ["borg_entities", "Graph nodes (typed, namespaced)", "Canonical", "✅"],
                  ["borg_entity_state", "Entity serving state (tier, salience, access)", "Derived", "✅"],
                  ["borg_facts", "Graph edges (temporal, with supersession)", "Canonical", "✅"],
                  ["borg_fact_state", "Fact serving state (salience, access)", "Derived", "✅"],
                  ["borg_procedures", "Candidate behavioral patterns", "Canonical", "✅"],
                  ["borg_predicates", "24 canonical relationship predicates", "Reference", "✅"],
                  ["borg_predicate_candidates", "Non-canonical predicates pending review", "Queue", "✅"],
                  ["borg_resolution_conflicts", "Ambiguous entity matches for review", "Queue", "✅"],
                  ["borg_namespace_config", "Per-namespace token budgets", "Config", "✅"],
                  ["borg_audit_log", "Full compilation + extraction traces", "Audit", "✅"],
                  ["borg_snapshots", "24h hot-tier state captures", "Snapshot", "✅"],
                ].map(([table, role, type, status]) => (
                  <tr key={table} className="border-b border-[var(--border)]/50">
                    <td className="py-3 pr-6 font-mono text-[var(--accent-green)] text-xs">{table}</td>
                    <td className="py-3 pr-6">{role}</td>
                    <td className="py-3 pr-6">
                      <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
                        type === "Canonical"
                          ? "bg-[var(--accent-green)]/10 text-[var(--accent-green)]"
                          : type === "Derived"
                          ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]"
                          : type === "Audit"
                          ? "bg-[var(--accent-amber)]/10 text-[var(--accent-amber)]"
                          : "bg-[var(--text-muted)]/10 text-[var(--text-muted)]"
                      }`}>
                        {type}
                      </span>
                    </td>
                    <td className="py-3">{status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
              borg_traverse()
            </h3>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)] mb-4">
              A recursive CTE function for 1-2 hop graph traversal. Cycle-safe via
              path tracking. Scoped to a single namespace. Used by the graph_neighborhood
              retrieval strategy.
            </p>
            <pre className="text-xs">
              <code>{`SELECT * FROM borg_traverse(
  p_entity_id := 'a1b2c3...',
  p_max_hops  := 2,
  p_namespace := 'product-engineering'
);
-- Returns: entity_id, entity_name, entity_type,
--          fact_id, predicate, evidence_status,
--          hop_depth, path`}</code>
            </pre>
          </div>
        </div>
      </Section>

      {/* API Surface */}
      <Section
        id="api"
        title="API Surface"
        subtitle="Three MCP tools + REST endpoints + admin. OSS release runs locally with no authentication."
        className="border-t border-[var(--border)]"
      >
        <div className="space-y-6">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Core
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Method</th>
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Path</th>
                    <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">Description</th>
                  </tr>
                </thead>
                <tbody className="text-[var(--text-secondary)]">
                  {[
                    ["POST", "/mcp", "MCP Streamable HTTP (borg_think, borg_learn, borg_recall)"],
                    ["POST", "/api/think", "Compile context (REST equivalent of borg_think)"],
                    ["POST", "/api/learn", "Ingest episode (REST equivalent of borg_learn)"],
                    ["POST", "/api/recall", "Search memory (REST equivalent of borg_recall)"],
                  ].map(([method, path, desc]) => (
                    <tr key={path} className="border-b border-[var(--border)]/50">
                      <td className="py-2 pr-6 font-mono text-xs text-[var(--accent-blue)]">{method}</td>
                      <td className="py-2 pr-6 font-mono text-xs text-[var(--accent-green)]">{path}</td>
                      <td className="py-2 text-xs">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Namespace Management
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Method</th>
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Path</th>
                    <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">Description</th>
                  </tr>
                </thead>
                <tbody className="text-[var(--text-secondary)]">
                  {[
                    ["GET", "/api/namespaces", "List all namespaces with budgets"],
                    ["GET", "/api/namespaces/:ns", "Get config + stats (entity/fact/episode/procedure counts)"],
                    ["POST", "/api/namespaces", "Create namespace with configurable budgets"],
                    ["PUT", "/api/namespaces/:ns", "Update budgets / description"],
                    ["DELETE", "/api/namespaces/:ns", "Delete (protects 'default')"],
                  ].map(([method, path, desc]) => (
                    <tr key={path + method} className="border-b border-[var(--border)]/50">
                      <td className="py-2 pr-6 font-mono text-xs text-[var(--accent-blue)]">{method}</td>
                      <td className="py-2 pr-6 font-mono text-xs text-[var(--accent-green)]">{path}</td>
                      <td className="py-2 text-xs">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Admin
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Method</th>
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Path</th>
                    <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">Description</th>
                  </tr>
                </thead>
                <tbody className="text-[var(--text-secondary)]">
                  {[
                    ["GET", "/api/admin/queue", "Processing queue depth + failed count"],
                    ["GET", "/api/admin/entities", "List entities (with tier, salience, access count)"],
                    ["GET", "/api/admin/facts", "List current facts (with salience + access tracking)"],
                    ["GET", "/api/admin/procedures", "List procedures (confidence + observation counts)"],
                    ["GET", "/api/admin/conflicts", "Unresolved entity resolution conflicts"],
                    ["GET", "/api/admin/predicates", "Canonical predicates + pending custom candidates"],
                    ["POST", "/api/admin/process-episode", "Manual extraction trigger"],
                    ["POST", "/api/admin/requeue-failed", "Requeue episodes with extraction errors"],
                    ["POST", "/api/admin/snapshot", "Manual hot-tier snapshot"],
                    ["GET", "/api/admin/cost-summary", "LLM token usage and estimated spend by namespace"],
                    ["GET", "/api/admin/snapshot/latest", "Most recent snapshot for a namespace"],
                  ].map(([method, path, desc]) => (
                    <tr key={path} className="border-b border-[var(--border)]/50">
                      <td className="py-2 pr-6 font-mono text-xs text-[var(--accent-blue)]">{method}</td>
                      <td className="py-2 pr-6 font-mono text-xs text-[var(--accent-green)]">{path}</td>
                      <td className="py-2 text-xs">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Section>

      <Section
        id="integration"
        title="Integrations"
        subtitle="Detailed client setup, AGENTS.md guidance, steering files, and MCP examples live on a dedicated page."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            This page focuses on runtime, schema, and API surface. Client setup for Claude Code,
            Codex CLI, Kiro, Claude Desktop, and REST ingestion now lives on the dedicated integrations page.
          </p>
          <div className="mt-5">
            <a
              href="/integrations"
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--border-accent)] px-5 py-3 text-sm font-semibold text-[var(--text-primary)] transition-all hover:border-[var(--accent-green)]/50 hover:bg-[var(--bg-primary)]"
            >
              Open Integrations
            </a>
          </div>
        </div>
      </Section>

      {/* Design Decisions */}
      <Section
        id="decisions"
        title="Design Decisions"
        subtitle="The constraints are intentional."
        className="border-t border-[var(--border)]"
      >
        <div className="space-y-4">
          {[
            {
              q: "Why LLM in the write path?",
              a: "Borg extracts structured knowledge (entities, typed facts, procedures) — not just text blobs. This requires an LLM. The trade-off is extraction cost and latency, but it runs offline so it never blocks queries. The alternative (embedding-only, like Ogham) gives you similarity search but not a queryable knowledge graph.",
            },
            {
              q: "Why not Neo4j / FalkorDB?",
              a: "Adding a graph database means syncing between two systems. Sync means drift. PostgreSQL recursive CTEs handle 1-2 hop traversal at the expected scale (hundreds of entities, thousands of facts). A dedicated graph DB is a measured-bottleneck escape hatch, not a starting point.",
            },
            {
              q: "Why three-pass resolution instead of always-merge?",
              a: "Collision is catastrophic — two different things merged corrupt every attached fact. Fragmentation is recoverable. The 0.92 semantic threshold is deliberately high. The 0.03 ambiguity gap flags uncertain matches for human review. You can always merge entities manually; you can never safely un-merge them.",
            },
            {
              q: "Why task-specific memory weights instead of one ranking?",
              a: "A debug task and a compliance audit need fundamentally different memory. Debug needs episodic recall (what happened?) and procedures (what patterns do I follow?). Compliance needs episodic evidence and semantic facts, but should never surface unverified procedures. One ranking can't serve both.",
            },
            {
              q: "Why two output formats, not a universal one?",
              a: "Claude handles structured XML with metadata attributes well. GPT prefers compact JSON. Sending XML to GPT wastes tokens on tags it doesn't need. Sending flat JSON to Claude loses the metadata Claude can reason about. Two formats, chosen by model parameter.",
            },
          ].map((item, i) => (
            <div
              key={i}
              className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6"
            >
              <h3 className="text-base font-semibold text-[var(--text-primary)]">
                {item.q}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
                {item.a}
              </p>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
