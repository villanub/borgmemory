import Link from "next/link";
import { FeatureCard } from "@/components/FeatureCard";
import { Section } from "@/components/Section";

export default function Home() {
  return (
    <>
      {/* Hero */}
      <div className="relative overflow-hidden pt-16">
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--accent-green)]/5 via-transparent to-transparent" />
        <div className="relative mx-auto max-w-6xl px-6 pb-20 pt-24">
          <div className="max-w-3xl">
            <Link
              href="/benchmarks"
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--accent-green)]/20 bg-[var(--accent-green)]/5 px-4 py-1.5 transition-all hover:bg-[var(--accent-green)]/10"
            >
              <span className="h-2 w-2 rounded-full bg-[var(--accent-green)] animate-pulse" />
              <span className="text-xs font-medium text-[var(--accent-green)]">
                10/10 task success | 91.3% precision | 78% less stale facts vs RAG →
              </span>
            </Link>

            <h1 className="text-5xl font-extrabold leading-tight tracking-tight text-[var(--text-primary)] sm:text-6xl">
              Your AI tools forget.
              <br />
              <span className="text-[var(--accent-green)] glow-green-text">
                Borg remembers.
              </span>
            </h1>

            <p className="mt-6 text-xl leading-relaxed text-[var(--text-secondary)]">
              Run one install command, type <code>borg init</code> in your project,
              and every AI coding session builds a knowledge graph that makes the
              next session smarter. One Postgres. No SDKs. No Neo4j.
            </p>

            <p className="mt-4 text-base text-[var(--text-muted)]">
              Open source. Apache 2.0. One local install.
            </p>

            <div className="mt-6 rounded-lg border border-[var(--accent-amber)]/30 bg-[var(--accent-amber)]/5 px-4 py-3 text-xs text-[var(--text-secondary)]">
              <span className="font-semibold text-[var(--accent-amber)]">Current release:</span>{" "}
              single-user, no auth, localhost only. Episodes are embedded and
              extracted via the OpenAI API (or your Azure OpenAI endpoint) —
              everything else stays on your machine. Not intended for shared
              deployments until auth lands.
            </div>

            <div className="mt-6 overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg-card)]">
              <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-2">
                <span className="text-xs text-[var(--text-muted)]">Quick start</span>
              </div>
              <pre className="!border-0 !rounded-none !m-0 px-4 py-3 text-sm leading-7">
                <code>{`curl -fsSL https://raw.githubusercontent.com/villanub/borgmemory/main/install.sh | sh
borg init`}</code>
              </pre>
            </div>

            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href="https://github.com/villanub/borgmemory"
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent-green)] px-6 py-3 text-sm font-semibold text-[var(--bg-primary)] transition-all hover:brightness-110"
              >
                Quick Start
              </Link>
              <Link
                href="/features"
                className="inline-flex items-center gap-2 rounded-lg border border-[var(--border-accent)] px-6 py-3 text-sm font-semibold text-[var(--text-primary)] transition-all hover:border-[var(--accent-green)]/50 hover:bg-[var(--bg-card)]"
              >
                Explore Features
              </Link>
            </div>
          </div>

          {/* Terminal preview */}
          <div className="mt-16 overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-card)] glow-green">
            <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-3">
              <span className="h-3 w-3 rounded-full bg-[var(--accent-red)]/60" />
              <span className="h-3 w-3 rounded-full bg-[var(--accent-amber)]/60" />
              <span className="h-3 w-3 rounded-full bg-[var(--accent-green)]/60" />
              <span className="ml-3 text-xs text-[var(--text-muted)]">
                Borg MCP across Codex, Claude Code, and Kiro
              </span>
            </div>
            <pre className="!border-0 !rounded-none !m-0 text-sm leading-7">
              <code>{`> "What patterns do I follow when debugging auth issues?"

borg_think → classify: debug (0.92) + architecture (0.31)
           → retrieve: graph_neighborhood + episode_recall + fact_lookup
           → rank: 14 candidates → 6 selected (1,840 tokens)
           → compile: structured XML

<borg model="claude" ns="product-engineering" task="debug">
  <knowledge>
    <fact status="observed" salience="0.94">Webhook gateway verifies HMAC signatures before enqueue</fact>
    <fact status="observed" salience="0.88">Background jobs retry with exponential backoff</fact>
  </knowledge>
  <episodes>
    <episode source="claude-code" date="2026-03-01">Fixed duplicate webhook delivery during replay</episode>
    <episode source="claude-code" date="2026-02-14">Resolved OAuth scope mismatch in staging</episode>
  </episodes>
  <patterns>
    <procedure confidence="0.92">Debug auth: verify scopes, then inspect token audience and issuer</procedure>
  </patterns>
</borg>`}</code>
            </pre>
          </div>
        </div>
      </div>

      {/* Feature grid */}
      <Section
        id="features"
        title="What Borg does differently"
        subtitle="Most memory tools store text and search by similarity. Borg extracts structured knowledge, builds a temporal graph, and compiles task-specific context packages."
      >
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <FeatureCard
            icon="⬡"
            title="Knowledge Graph Extraction"
            description="An LLM pipeline extracts entities, facts, and procedures from every conversation. Three-pass entity resolution prevents collisions. 24 canonical predicates ensure consistent relationships."
            detail="Entities are resolved by exact match → alias match → semantic similarity (0.92 threshold). Fragmentation is preferred over collision — two separate entities can be merged later."
          />
          <FeatureCard
            icon="⏱"
            title="Temporal Facts with Supersession"
            description="Facts carry valid_from and valid_until timestamps. When a new fact contradicts an old one, the old fact is marked superseded — not deleted. The full history is always available for compliance queries."
            detail="Seven evidence statuses: user_asserted, observed, extracted, inferred, promoted, deprecated, superseded."
          />
          <FeatureCard
            icon="🎯"
            title="Task-Specific Compilation"
            description="Dual-profile intent classification determines what kind of memory a query needs. Debug tasks get episodic + procedural memory. Architecture tasks get semantic facts. Compliance tasks exclude procedural entirely."
            detail="Memory-type weight modifiers bias ranking without hard exclusion (except procedural in compliance where weight = 0.0)."
          />
          <FeatureCard
            icon="📊"
            title="Inspectable Ranking"
            description="Every candidate is scored on four dimensions: relevance, recency, stability, and provenance. Every compilation logs which items were selected, which were rejected, and why."
            detail="The audit log is the primary tool for improving retrieval quality. No opaque composite scores."
          />
          <FeatureCard
            icon="🔒"
            title="Namespace Isolation"
            description="Hard isolation by default. Every entity, fact, and episode belongs to exactly one namespace. No cross-namespace queries. Configurable token budgets per namespace."
            detail="If 'APIM' appears in two projects, it exists as two separate entity records. Restrictive by design — cross-namespace is a future feature, not an accident."
          />
          <FeatureCard
            icon="🐘"
            title="PostgreSQL Maximalism"
            description="One database, no exceptions. Graph traversal via recursive CTEs. Embeddings via pgvector. Audit via pgAudit. No external graph database, no separate vector store. Nothing gets out of sync."
            detail="15 tables + 1 function. Runs on Azure PostgreSQL Flexible Server, Supabase, Neon, or any Postgres 14+."
          />
        </div>
      </Section>

      {/* How it works */}
      <Section
        id="how-it-works"
        title="How it works"
        subtitle="Two pipelines that share a database but never share runtime. Online never waits for offline."
        className="border-t border-[var(--border)]"
      >
        <div className="grid gap-12 lg:grid-cols-2">
          {/* Online pipeline */}
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--accent-green)]/20 bg-[var(--accent-green)]/10 px-3 py-1">
              <span className="text-xs font-semibold text-[var(--accent-green)]">
                ONLINE PIPELINE
              </span>
            </div>
            <p className="mb-6 text-sm text-[var(--text-secondary)]">
              Serves <code>borg_think</code> queries. Latency-sensitive. Compiles
              context in real time.
            </p>
            <div className="space-y-5">
              {[
                ["Classify intent", "Dual-profile — primary + secondary task class with confidence scores. Both profiles run retrieval."],
                ["Retrieve candidates", "Up to 3 strategies in parallel: fact lookup, episode recall, graph neighborhood, procedure assist. Vector search when embeddings exist, recency fallback otherwise."],
                ["Rank and trim", "4-dimension scoring (relevance × type weight, recency, stability + salience, provenance). Dedup by content. Trim to namespace token budget."],
                ["Compile package", "Structured XML for Claude/Copilot, compact JSON for GPT/Codex. Model assignment via parameter."],
                ["Update access tracking", "Batch-update entity_state and fact_state for selected candidates. Feeds hot-tier promotion."],
                ["Audit log", "Full trace: classification, profiles executed, score breakdowns, rejection reasons, latency per stage."],
              ].map(([title, desc], i) => (
                <div key={i} className="pipeline-step">
                  <h4 className="text-sm font-semibold text-[var(--text-primary)]">
                    {i + 1}. {title}
                  </h4>
                  <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">
                    {desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Offline pipeline */}
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--accent-blue)]/20 bg-[var(--accent-blue)]/10 px-3 py-1">
              <span className="text-xs font-semibold text-[var(--accent-blue)]">
                OFFLINE PIPELINE
              </span>
            </div>
            <p className="mb-6 text-sm text-[var(--text-secondary)]">
              Processes episodes via <code>borg_learn</code>. Runs asynchronously.
              Never blocks queries.
            </p>
            <div className="space-y-5">
              {[
                ["Ingest + dedup", "SHA-256 content hash + source_event_id unique constraint. Duplicate episodes return existing ID."],
                ["Generate embedding", "Azure OpenAI text-embedding-3-small (1536-dim). Gracefully skips if not configured."],
                ["Extract entities", "LLM extracts up to 10 entities per episode with typed taxonomy and aliases."],
                ["Resolve entities", "Three-pass: exact match → alias match → semantic (0.92 threshold). Ambiguous matches flagged as conflicts."],
                ["Extract facts + validate predicates", "LLM extracts up to 8 fact triples. Predicates validated against 24-predicate canonical registry. Custom predicates tracked."],
                ["Supersession check", "Same subject + predicate + different object → old fact marked superseded with valid_until."],
                ["Extract procedures", "LLM extracts up to 3 repeatable patterns. Existing patterns merged (observation count bumped, confidence averaged)."],
                ["Snapshot", "Every 24h, hot-tier state captured for all namespaces. Enables cold-start and drift detection."],
              ].map(([title, desc], i) => (
                <div key={i} className="pipeline-step">
                  <h4 className="text-sm font-semibold text-[var(--text-primary)]">
                    {i + 1}. {title}
                  </h4>
                  <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">
                    {desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* MCP tools */}
      <Section
        id="mcp"
        title="Three MCP tools"
        subtitle="Not five. Three tools that cover the entire interaction surface."
        className="border-t border-[var(--border)]"
      >
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <code className="text-lg font-bold text-[var(--accent-green)]">
              borg_think
            </code>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              Compile context for a query. Runs the full online pipeline — classify,
              retrieve, rank, compile. Returns structured or compact context package.
            </p>
            <pre className="mt-4 text-xs">
              <code>{`borg_think(
  query: "debug webhook delivery timeout",
  namespace: "product-engineering",
  model: "claude",
  task_hint: "debug"
)`}</code>
            </pre>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <code className="text-lg font-bold text-[var(--accent-blue)]">
              borg_learn
            </code>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              Record a decision, discovery, or conversation. Stored immediately,
              extraction happens in the background. Returns in milliseconds.
            </p>
            <pre className="mt-4 text-xs">
              <code>{`borg_learn(
  content: "Decided to version event payloads through a schema registry...",
  source: "claude-code",
  namespace: "product-engineering"
)`}</code>
            </pre>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <code className="text-lg font-bold text-[var(--accent-amber)]">
              borg_recall
            </code>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              Search memory directly without compilation. Returns raw episodes,
              facts, and procedures. For when you want to browse, not compile.
            </p>
            <pre className="mt-4 text-xs">
              <code>{`borg_recall(
  query: "release checklist",
  namespace: "product-engineering",
  memory_type: "semantic"
)`}</code>
            </pre>
          </div>
        </div>
      </Section>

      {/* Try it */}
      <Section
        id="try-it"
        title="Try it"
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-8">
          <pre className="!border-0 !bg-transparent !p-0 text-sm leading-8">
            <code>{`# In Codex, Claude Code, or Kiro with Borg connected:
> "Remember that preview environments expire after 7 days unless renewed"

  borg_learn → episode accepted, queued for extraction
  → worker: embedded, 2 entities extracted, 1 fact created

# Later, in the same client or a different one:
> "What's our preview environment policy?"

  borg_think → classify: architecture (0.87)
            → fact_lookup: "Preview environments expire after 7 days unless renewed"
            → compiled into context package (340 tokens)

# It works across clients because they all hit the same PostgreSQL database.`}</code>
          </pre>
        </div>
      </Section>

      {/* Stack */}
      <Section
        id="stack"
        title="The stack"
        className="border-t border-[var(--border)]"
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "API Runtime", value: "FastAPI + FastMCP 3", sub: "Streamable HTTP MCP and REST on :8080" },
            { label: "Auth", value: "Passthrough", sub: "No authentication — single-user, local deployment" },
            { label: "Database", value: "PostgreSQL 14+", sub: "Knowledge graph, pgvector embeddings, and audit trail" },
            { label: "Extraction", value: "OpenAI / Azure OpenAI", sub: "Supports both standard OpenAI and Azure OpenAI endpoints" },
          ].map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-5"
            >
              <p className="text-xs font-medium uppercase tracking-wider text-[var(--text-muted)]">
                {item.label}
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--text-primary)]">
                {item.value}
              </p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                {item.sub}
              </p>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}
