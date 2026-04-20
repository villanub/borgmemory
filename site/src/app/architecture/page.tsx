import { PageHero, Crosslinks } from "@/components/Section";

const SCHEMA: { tbl: string; role: string; type: "Canonical" | "Derived" | "Audit" | "Reference" | "Queue" | "Config" | "Snapshot"; status: string }[] = [
  { tbl: "borg_episodes", role: "Immutable evidence layer", type: "Canonical", status: "✓ ships" },
  { tbl: "borg_entities", role: "Graph nodes — typed, namespaced", type: "Canonical", status: "✓ ships" },
  { tbl: "borg_entity_state", role: "Tier, salience, access counters", type: "Derived", status: "✓ ships" },
  { tbl: "borg_facts", role: "Graph edges — temporal, with supersession", type: "Canonical", status: "✓ ships" },
  { tbl: "borg_fact_state", role: "Salience + access for facts", type: "Derived", status: "✓ ships" },
  { tbl: "borg_procedures", role: "Candidate behavioral patterns", type: "Canonical", status: "✓ ships" },
  { tbl: "borg_predicates", role: "24 canonical relationship verbs", type: "Reference", status: "✓ ships" },
  { tbl: "borg_predicate_candidates", role: "Non-canonical, pending review", type: "Queue", status: "✓ ships" },
  { tbl: "borg_resolution_conflicts", role: "Ambiguous entity matches", type: "Queue", status: "✓ ships" },
  { tbl: "borg_namespace_config", role: "Per-namespace token budgets", type: "Config", status: "✓ ships" },
  { tbl: "borg_audit_log", role: "Full compile + extraction traces", type: "Audit", status: "✓ ships" },
  { tbl: "borg_snapshots", role: "24 h hot-tier state captures", type: "Snapshot", status: "✓ ships" },
];

const DECISIONS: { q: string; a: React.ReactNode }[] = [
  {
    q: "Why LLM in the write path?",
    a: (
      <>
        Borg extracts structured knowledge — not text blobs. That requires an
        LLM. The cost is extraction latency and tokens; the mitigation is that
        it runs entirely offline and never blocks <code>borg_think</code>. The
        alternative (embed-only) gives you similarity search but not a
        queryable graph.
      </>
    ),
  },
  {
    q: "Why not Neo4j or FalkorDB?",
    a: (
      <>
        Adding a graph DB means syncing two systems. Sync means drift.
        PostgreSQL recursive CTEs handle 1–2 hop traversal at the expected
        scale (hundreds of entities, thousands of facts). A dedicated graph DB
        is a measured-bottleneck escape hatch, not a starting point.
      </>
    ),
  },
  {
    q: "Why three-pass resolution, not always-merge?",
    a: (
      <>
        Collision is catastrophic. Fragmentation is recoverable. The 0.92
        semantic threshold is deliberately high. The 0.03 ambiguity gap flags
        uncertain matches for human review. You can merge entities manually;
        you can never safely un-merge them.
      </>
    ),
  },
  {
    q: "Why per-task memory weights, not one ranking?",
    a: (
      <>
        Debug needs episodic recall and procedures. Compliance needs episodic
        evidence and semantic facts, but should never surface unverified
        procedures. One ranking can&apos;t serve both — so the weights change
        per task, not the code.
      </>
    ),
  },
  {
    q: "Why two output formats?",
    a: (
      <>
        Claude reasons over structured XML attributes. GPT prefers compact
        JSON. Sending XML to GPT wastes tokens on tags it ignores; sending flat
        JSON to Claude loses metadata Claude uses. Two formats, chosen by the{" "}
        <code>model</code> parameter.
      </>
    ),
  },
];

export default function ArchitecturePage() {
  return (
    <>
      <PageHero
        num="§ /architecture — 15 tables · 1 function · one postgres"
        title={
          <>
            One container.
            <br />
            One database.
            <br />
            <em>Two pipelines.</em>
          </>
        }
        lede="System design, schema, API surface, and the decisions behind each constraint. Runs locally against any Postgres 14+."
        meta={[
          { label: "read", value: "10 min" },
          { label: "db", value: "PostgreSQL 14+" },
          { label: "ports", value: "8080/mcp · 8080/api" },
        ]}
      />

      <div className="jump">
        <div className="wrap inner">
          <span className="label">§ jump to</span>
          <a href="#topology">Topology</a>
          <a href="#schema">Schema</a>
          <a href="#api">API</a>
          <a href="#decisions">Decisions</a>
        </div>
      </div>

      <section className="block" id="topology">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 01 — TOPOLOGY</div>
              <h2>
                Runtime, <em>in three boxes.</em>
              </h2>
            </div>
            <p className="sub">
              A single <code>borg-engine</code> process talks MCP and REST on{" "}
              <code>:8080</code>. It reads from and writes to one Postgres, and
              calls out to OpenAI or Azure OpenAI only for extraction and
              embeddings.
            </p>
          </div>

          <div className="topo">
            <div className="node">
              <span className="port">:8080</span>
              <span className="tag">engine</span>
              <h4>borg-engine</h4>
              <ul>
                <li>FastAPI + FastMCP 3</li>
                <li>
                  MCP endpoint{" "}
                  <span className="mono" style={{ color: "var(--ink-3)" }}>
                    /mcp
                  </span>
                </li>
                <li>
                  REST{" "}
                  <span className="mono" style={{ color: "var(--ink-3)" }}>
                    /api/&#123;think,learn,recall&#125;
                  </span>
                </li>
                <li>Background extraction worker</li>
                <li>24 h snapshot loop</li>
              </ul>
            </div>

            <div className="node pg">
              <span className="tag" style={{ color: "var(--accent)" }}>
                source of truth
              </span>
              <h4>
                PostgreSQL <em>14+</em>
              </h4>
              <ul>
                <li>pgvector, pgAudit, uuid-ossp</li>
                <li>
                  borg_* tables — <b>15 + 1 fn</b>
                </li>
                <li>Managed · self-hosted · local</li>
                <li>Recursive CTE traversal</li>
              </ul>
            </div>

            <div className="node">
              <span className="tag">extraction</span>
              <h4>OpenAI · Azure OpenAI</h4>
              <ul>
                <li>
                  <span className="mono" style={{ color: "var(--ink-3)" }}>
                    text-embedding-3-small
                  </span>{" "}
                  — 1 536-dim
                </li>
                <li>
                  <span className="mono" style={{ color: "var(--ink-3)" }}>
                    gpt-5-mini
                  </span>{" "}
                  /{" "}
                  <span className="mono" style={{ color: "var(--ink-3)" }}>
                    gpt-4o-mini
                  </span>
                </li>
                <li>
                  BYO key. Off-loaded async — never blocks{" "}
                  <code>borg_think</code>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="schema">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 02 — SCHEMA</div>
              <h2>
                Fifteen tables.
                <br />
                <em>One function.</em>
              </h2>
            </div>
            <p className="sub">
              Every table cleanly separates canonical data from derived serving
              state. Hot-path denormalization lives in <code>*_state</code>,
              the source of truth in the parent table.
            </p>
          </div>

          <div className="card" style={{ padding: "10px 26px" }}>
            <div
              className="schema-row"
              style={{
                borderBottom: "1px solid var(--line-2)",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                color: "var(--ink-3)",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                padding: "14px 0",
              }}
            >
              <span>Table</span>
              <span>Role</span>
              <span>Type</span>
              <span>Status</span>
            </div>
            {SCHEMA.map((r) => (
              <div key={r.tbl} className="schema-row">
                <span className="tbl">{r.tbl}</span>
                <span className="role">{r.role}</span>
                <span className={`type ${r.type.toLowerCase()}`}>{r.type}</span>
                <span className="status">{r.status}</span>
              </div>
            ))}
          </div>

          <div className="card" style={{ marginTop: 20 }}>
            <h3>
              borg_traverse() — <em>recursive CTE function</em>
            </h3>
            <p>
              Used by the graph_neighborhood retrieval strategy. 1–2 hop
              traversal, cycle-safe via path tracking, scoped to a single
              namespace.
            </p>
            <pre>
              <span className="c">
                -- 1-2 hop graph walk, cycle-safe, ns-scoped
              </span>
              {"\n"}
              SELECT * FROM <span className="k">borg_traverse</span>({"\n"}
              {"  "}p_entity_id := &apos;a1b2c3…&apos;,{"\n"}
              {"  "}p_max_hops := 2,{"\n"}
              {"  "}p_namespace := &apos;product-engineering&apos;{"\n"}
              );{"\n"}
              <span className="c">
                -- returns: entity_id, entity_name, entity_type,{"\n"}
                -- fact_id, predicate, evidence_status,{"\n"}
                -- hop_depth, path
              </span>
            </pre>
          </div>
        </div>
      </section>

      <section className="block" id="api">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 03 — API SURFACE</div>
              <h2>
                Three MCP tools.
                <br />
                <em>REST mirror. Admin.</em>
              </h2>
            </div>
            <p className="sub">
              OSS release runs locally with no authentication — single-user by
              design. Auth for shared deployments is on the roadmap; the schema
              already supports it.
            </p>
          </div>

          <div className="split-3">
            <div className="card">
              <div className="kicker" style={{ color: "var(--accent)", marginBottom: 10 }}>
                core — mcp + rest
              </div>
              <table className="etable">
                <tbody>
                  <tr>
                    <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                      POST
                    </td>
                    <td className="mono">/mcp</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                      POST
                    </td>
                    <td className="mono">/api/think</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                      POST
                    </td>
                    <td className="mono">/api/learn</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                      POST
                    </td>
                    <td className="mono">/api/recall</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="card">
              <div className="kicker" style={{ color: "var(--accent)", marginBottom: 10 }}>
                namespaces
              </div>
              <table className="etable">
                <tbody>
                  <tr>
                    <td className="mono" style={{ color: "var(--accent)" }}>
                      GET
                    </td>
                    <td className="mono">/api/namespaces</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "var(--accent)" }}>
                      GET
                    </td>
                    <td className="mono">/api/namespaces/:ns</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                      POST
                    </td>
                    <td className="mono">/api/namespaces</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "var(--warn)" }}>
                      PUT
                    </td>
                    <td className="mono">/api/namespaces/:ns</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "var(--danger)" }}>
                      DEL
                    </td>
                    <td className="mono">/api/namespaces/:ns</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="card">
              <div className="kicker" style={{ color: "var(--accent)", marginBottom: 10 }}>
                admin
              </div>
              <table className="etable">
                <tbody>
                  <tr>
                    <td className="mono" style={{ color: "var(--accent)" }}>
                      GET
                    </td>
                    <td className="mono">/api/admin/queue</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "var(--accent)" }}>
                      GET
                    </td>
                    <td className="mono">/api/admin/entities</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "var(--accent)" }}>
                      GET
                    </td>
                    <td className="mono">/api/admin/facts</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "var(--accent)" }}>
                      GET
                    </td>
                    <td className="mono">/api/admin/procedures</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "var(--accent)" }}>
                      GET
                    </td>
                    <td className="mono">/api/admin/conflicts</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "var(--accent)" }}>
                      GET
                    </td>
                    <td className="mono">/api/admin/predicates</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                      POST
                    </td>
                    <td className="mono">/admin/process-episode</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                      POST
                    </td>
                    <td className="mono">/admin/requeue-failed</td>
                  </tr>
                  <tr>
                    <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                      POST
                    </td>
                    <td className="mono">/admin/snapshot</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="decisions">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 04 — DECISIONS</div>
              <h2>
                The constraints
                <br />
                <em>are intentional.</em>
              </h2>
            </div>
            <p className="sub">
              Every choice below has a failure mode it prevents and a cost it
              accepts. If you disagree,{" "}
              <a
                href="https://github.com/villanub/borgmemory/issues"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "var(--accent)" }}
              >
                file an issue
              </a>
              .
            </p>
          </div>

          <div className="card" style={{ padding: "0 28px" }}>
            {DECISIONS.map((d, i) => (
              <div key={i} className="decision">
                <div className="q">{d.q}</div>
                <div className="a">{d.a}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Crosslinks
        left={{
          kicker: "/features",
          href: "/features",
          title: (
            <>
              Features, <em>with tradeoffs.</em>
            </>
          ),
          body: "Every capability plus the decision it implies. Fragmentation over collision. Supersession over overwrite.",
        }}
        right={{
          kicker: "/science",
          href: "/science",
          title: (
            <>
              <em>Why</em> this works.
            </>
          ),
          body: "Cognitive science, record linkage, bitemporal data, and why memory is a compilation problem — not a search one.",
        }}
      />
    </>
  );
}
