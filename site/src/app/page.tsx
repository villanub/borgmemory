import Link from "next/link";
import { ProofStrip } from "@/components/ProofStrip";
import { Ticker } from "@/components/Ticker";
import { GraphViz } from "@/components/GraphViz";
import { CompileDemo } from "@/components/CompileDemo";
import { BenchBars } from "@/components/BenchBars";
import { Install } from "@/components/Install";

export default function Home() {
  return (
    <>
      {/* ─── Hero (weird variant) ──────────────────────────────────────── */}
      <section className="hero">
        <div className="glow" />
        <div className="wrap">
          <div className="stack">
            <div>
              <div className="eyebrow">
                <span className="pill">
                  <span className="dot" />
                  session #00417 · live
                </span>
              </div>
              <h1>
                A <em>memory stronghold</em> for your AI coding agent.
              </h1>
              <p className="lede">
                Install once. Every session your agent has — Claude Code, Codex,
                Copilot, Kiro — flows into one Postgres knowledge graph. Next
                session, it walks in already briefed.
              </p>
              <Install />
              <div className="sub-ctas" style={{ marginTop: 22 }}>
                <a href="#compile">how it works</a>
                <a href="#bench">the bench</a>
                <a href="#cmp">vs. mem0 · zep · cognee</a>
              </div>
            </div>
            <div className="weird-side">
              <div className="kicker">What Borg knows about this project, right now</div>
              <GraphViz />
            </div>
          </div>
        </div>
      </section>

      {/* ─── Proof strip ────────────────────────────────────────────────── */}
      <ProofStrip />

      {/* ─── Ticker ─────────────────────────────────────────────────────── */}
      <Ticker />

      {/* ─── § 01 — THE LOOP / compile demo ─────────────────────────────── */}
      <section className="block" id="compile">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 01 — THE LOOP</div>
              <h2>
                Not search.
                <br />
                <em>Compilation.</em>
              </h2>
            </div>
            <p className="sub">
              Every <span className="mono">borg_think</span> call runs the same
              five-stage pipeline: classify the intent, retrieve across facts /
              episodes / graph, rank on four dimensions, compile for the target
              model, log the trace. You see every candidate and why it was
              picked or rejected.
            </p>
          </div>
          <CompileDemo />
        </div>
      </section>

      {/* ─── § 02 — WHAT'S INSIDE / features list ───────────────────────── */}
      <section className="block" id="features">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 02 — WHAT&apos;S INSIDE</div>
              <h2>
                Six decisions,
                <br />
                <em>one system.</em>
              </h2>
            </div>
            <p className="sub">
              Every choice below ships in the open-source release under Apache
              2.0. Read the full tradeoffs on{" "}
              <Link href="/features" style={{ color: "var(--accent)" }}>
                /features
              </Link>
              .
            </p>
          </div>
          <div className="features">
            {FEATURES.map((f) => (
              <div className="feat" key={f.n}>
                <div className="idx">{f.n}</div>
                <h3>{f.title}</h3>
                <div className="body">
                  {f.body}
                  <div className="tag">↳ {f.tag}</div>
                </div>
                <div className="spec">
                  {f.specs.map((s, i) => (
                    <div key={i}>
                      {s[0]} · <b>{s[1]}</b>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── § 03 — MCP SURFACE ─────────────────────────────────────────── */}
      <section className="block" id="mcp">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 03 — MCP SURFACE</div>
              <h2>
                Three tools.
                <br />
                <em>Not five.</em>
              </h2>
            </div>
            <p className="sub">
              The entire interaction surface is three MCP tools. Works unchanged
              across Claude Code, Codex CLI, Copilot, Kiro, and anything else
              that speaks MCP over streamable HTTP.
            </p>
          </div>
          <div className="mcp">
            {MCP_TOOLS.map((t) => (
              <div className="tool" key={t.name}>
                <div className="head">
                  <span className="name">{t.name}</span>
                  <span className="role">{t.role}</span>
                </div>
                <p className="desc">{t.desc}</p>
                <pre>{t.code}</pre>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── § 04 — THE LANDSCAPE / comparison ──────────────────────────── */}
      <section className="block" id="cmp">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 04 — THE LANDSCAPE</div>
              <h2>
                Everyone else returns results.
                <br />
                <em>Borg returns context.</em>
              </h2>
            </div>
            <p className="sub">
              Every competitor wraps 2–3 databases and hands the agent raw
              matches. Borg is one Postgres that compiles.
            </p>
          </div>
          <table className="cmp">
            <thead>
              <tr>
                <th> </th>
                <th>Mem0</th>
                <th>Zep</th>
                <th>Cognee</th>
                <th className="us">Borg</th>
              </tr>
            </thead>
            <tbody>
              {COMPARE.map((r, i) => (
                <tr key={i}>
                  <th>{r[0]}</th>
                  <td className="no">{r[1]}</td>
                  <td className="no">{r[2]}</td>
                  <td className="no">{r[3]}</td>
                  <td className="us yes">{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ─── § 05 — THE BENCH ──────────────────────────────────────────── */}
      <section className="block" id="bench">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 05 — THE BENCH</div>
              <h2>
                Ten tasks.
                <br />
                <em>Three conditions.</em>
              </h2>
            </div>
            <p className="sub">
              Modeled on real cloud-infrastructure engineering work — incident
              response, schema migration, architecture review. Each condition
              runs the same evaluator against the same ground-truth labels.
              Seeds + code:{" "}
              <span className="mono" style={{ color: "var(--ink-2)" }}>
                /bench
              </span>
              .
            </p>
          </div>
          <BenchBars />
        </div>
      </section>

      {/* ─── § 06 — GO DEEPER ───────────────────────────────────────────── */}
      <section className="block" id="pages">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 06 — GO DEEPER</div>
              <h2>
                Three long reads.
                <br />
                <em>One system.</em>
              </h2>
            </div>
            <p className="sub">
              Written for staff engineers and eng leaders. No buzzwords, no
              emoji, no filler.
            </p>
          </div>
          <div className="pages">
            {DEEPER.map((c, i) => (
              <Link className="page-card" href={c.href} key={i}>
                <span className="kicker">{c.kicker}</span>
                <h4>{c.title}</h4>
                <p>{c.body}</p>
                <span className="more">
                  open <span>↗</span>
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA — install it now ───────────────────────────────────────── */}
      <section className="block" style={{ background: "var(--bg-2)" }}>
        <div className="wrap-tight" style={{ textAlign: "center" }}>
          <div className="kicker" style={{ marginBottom: 20 }}>
            — install it now —
          </div>
          <h2
            style={{
              fontSize: "clamp(36px, 5vw, 64px)",
              fontWeight: 500,
              letterSpacing: "-0.03em",
              lineHeight: 1.05,
              margin: "0 0 20px",
            }}
          >
            One command. One{" "}
            <em
              style={{
                fontFamily: "var(--font-serif)",
                fontStyle: "italic",
                fontWeight: 400,
                color: "var(--accent)",
              }}
            >
              Postgres.
            </em>
            <br />
            Every session after, smarter.
          </h2>
          <p
            style={{
              color: "var(--ink-2)",
              fontSize: 18,
              maxWidth: 620,
              margin: "0 auto 36px",
            }}
          >
            Apache 2.0. Single-user, local-first, bring your own key.
            Shared-deployment auth is on the roadmap.
          </p>
          <div style={{ maxWidth: 820, margin: "0 auto" }}>
            <Install />
          </div>
          <div
            style={{
              marginTop: 20,
              fontFamily: "var(--font-mono)",
              fontSize: 12,
              color: "var(--ink-3)",
            }}
          >
            <a
              href="https://github.com/villanub/borgmemory"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "var(--ink-2)", borderBottom: "1px solid var(--line-2)" }}
            >
              view on github
            </a>
          </div>
        </div>
      </section>
    </>
  );
}

/* ──────────────── Data ──────────────── */

const FEATURES: {
  n: string;
  title: React.ReactNode;
  body: React.ReactNode;
  tag: string;
  specs: [string, string][];
}[] = [
  {
    n: "01",
    title: "Knowledge Graph Extraction",
    body: "An LLM pipeline turns conversations into typed entities, temporal facts, and reusable procedures — with three-pass resolution that prefers fragmentation over collision.",
    tag: "Graph is mergeable. Collisions are not.",
    specs: [
      ["MODEL", "gpt-5-mini"],
      ["CAP", "10 entities / ep."],
      ["THRESH", "0.92 semantic"],
    ],
  },
  {
    n: "02",
    title: "Temporal Facts with Supersession",
    body: (
      <>
        Every fact carries <span className="mono">valid_from</span> and{" "}
        <span className="mono">valid_until</span>. New contradictions mark old
        facts superseded — never deleted. Compliance queries still see history;
        working memory doesn&apos;t.
      </>
    ),
    tag: "78% fewer stale facts in bench C vs RAG.",
    specs: [
      ["STATUSES", "7"],
      ["PREDICATES", "24 canonical"],
      ["HISTORY", "bitemporal"],
    ],
  },
  {
    n: "03",
    title: "Task-Specific Compilation",
    body: "Dual-profile intent classification picks what kind of memory a query needs. Debug gets episodic + procedural. Architecture gets semantic facts. Compliance excludes procedural entirely.",
    tag: "Weights bias ranking, not hard excludes.",
    specs: [
      ["PROFILES", "2"],
      ["FORMATS", "XML · JSON"],
      ["BUDGET", "per namespace"],
    ],
  },
  {
    n: "04",
    title: "Inspectable Ranking",
    body: "Four orthogonal scores — relevance, recency, stability, provenance — surfaced individually. Every compilation emits an audit trail of selected, rejected, and why. No opaque composites.",
    tag: "The audit log is the debugger.",
    specs: [
      ["DIMENSIONS", "4"],
      ["AUDIT", "pgAudit"],
      ["OPS", "insert · select"],
    ],
  },
  {
    n: "05",
    title: "Namespace Isolation",
    body: "Hard by default: every entity, fact, and episode belongs to exactly one namespace. No cross-namespace queries. Per-namespace token budgets. Projects stay cleanly separate.",
    tag: "Cross-ns is a future feature, not an accident.",
    specs: [
      ["MODE", "hard"],
      ["BUDGETS", "token-per-ns"],
      ["LEAK", "structurally impossible"],
    ],
  },
  {
    n: "06",
    title: "PostgreSQL Maximalism",
    body: "One database. Graph via recursive CTE. Embeddings via pgvector. Audit via pgAudit. No Qdrant. No Neo4j. No sync daemons. Runs on Supabase, Neon, managed Postgres, or your laptop.",
    tag: "Nothing gets out of sync if there is nothing to sync.",
    specs: [
      ["TABLES", "15 + 1 fn"],
      ["EXT", "pgvector · pgAudit"],
      ["MIN", "PG 14"],
    ],
  },
];

const MCP_TOOLS: { name: string; role: string; desc: string; code: React.ReactNode }[] = [
  {
    name: "borg_think",
    role: "compile",
    desc: "Compile context for a query. Runs the full online pipeline — classify, retrieve, rank, compile — and returns a ranked, token-budgeted context package.",
    code: (
      <>
        <span className="k">borg_think</span>(<br />
        {"  "}
        <span className="s">query</span>: &quot;debug webhook delivery timeout&quot;,
        <br />
        {"  "}
        <span className="s">namespace</span>: &quot;product-engineering&quot;,
        <br />
        {"  "}
        <span className="s">model</span>: &quot;claude&quot;,
        <br />
        {"  "}
        <span className="s">task_hint</span>: &quot;debug&quot;
        <br />)
      </>
    ),
  },
  {
    name: "borg_learn",
    role: "record",
    desc: "Record a decision or discovery. Stored immediately, extraction runs async. Returns in milliseconds so nothing blocks the agent loop.",
    code: (
      <>
        <span className="k">borg_learn</span>(<br />
        {"  "}
        <span className="s">content</span>: &quot;Versioned event payloads via schema registry…&quot;,
        <br />
        {"  "}
        <span className="s">source</span>: &quot;claude-code&quot;,
        <br />
        {"  "}
        <span className="s">namespace</span>: &quot;product-engineering&quot;
        <br />)
      </>
    ),
  },
  {
    name: "borg_recall",
    role: "browse",
    desc: "Direct memory search without compilation. Raw episodes, facts, and procedures — for UI, audits, or you-the-developer.",
    code: (
      <>
        <span className="k">borg_recall</span>(<br />
        {"  "}
        <span className="s">query</span>: &quot;release checklist&quot;,
        <br />
        {"  "}
        <span className="s">namespace</span>: &quot;product-engineering&quot;,
        <br />
        {"  "}
        <span className="s">memory_type</span>: &quot;semantic&quot;
        <br />)
      </>
    ),
  },
];

const COMPARE: [string, string, string, string, string][] = [
  ["Databases required", "Qdrant + Neo4j", "Neo4j + vectors", "3+", "1 · Postgres"],
  ["Integration", "Python SDK", "Python SDK", "Python SDK", "1 line in CLAUDE.md"],
  ["Retrieval output", "Raw results", "Raw results", "Raw results", "Compiled ranked context"],
  ["Stale-fact handling", "None", "Temporal (Neo4j)", "None", "Temporal · supersession"],
  ["Cross-client reuse", "Per SDK", "Per SDK", "Per SDK", "Any MCP client, same DB"],
  ["Audit + inspect", "Limited", "Partial", "Limited", "Full trace, per compile"],
  ["License", "Source-avail.", "Mixed", "Open", "Apache 2.0"],
];

const DEEPER: { kicker: string; href: string; title: React.ReactNode; body: string }[] = [
  {
    kicker: "/features",
    href: "/features",
    title: (
      <>
        Features, <em>with tradeoffs.</em>
      </>
    ),
    body: "Every capability plus the decision it implies. Read why fragmentation beats collision, how supersession settles contradictions, and where the 24 predicates come from.",
  },
  {
    kicker: "/architecture",
    href: "/architecture",
    title: (
      <>
        15 tables. <em>One schema.</em>
      </>
    ),
    body: "Reference layout, end-to-end schema, deployment topology, failure modes. Every table separates canonical data from serving state.",
  },
  {
    kicker: "/science",
    href: "/science",
    title: (
      <>
        <em>Why</em> this works.
      </>
    ),
    body: "Grounded in Tulving's episodic/semantic split, Fellegi-Sunter record linkage, bitemporal data, and the Lost-in-the-Middle paper. Memory is not a search problem.",
  },
];
