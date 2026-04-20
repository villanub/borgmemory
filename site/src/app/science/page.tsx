import { PageHero, Crosslinks } from "@/components/Section";

const PRINCIPLES: { anchor: string; title: React.ReactNode; body: React.ReactNode }[] = [
  {
    anchor: "Tulving's episodic + semantic memory model",
    title: "Evidence-grounded memory",
    body: (
      <>
        Borg treats conversations as episodic memory and extracted facts as
        semantic memory. The offline pipeline turns raw episodes into
        structured facts, procedures, and entities — each with provenance.
        That gives the system something it can <em>compare, supersede, and
        rank</em>, instead of treating an old conversation chunk as permanent
        truth.
      </>
    ),
  },
  {
    anchor: "Fellegi–Sunter record linkage",
    title: (
      <>
        Prefer fragmentation <em>over collision</em>
      </>
    ),
    body: (
      <>
        When entity resolution is uncertain, Borg keeps two references
        separate rather than merging the wrong things. A false merge poisons
        every downstream fact. A temporary split is inconvenient but
        recoverable. That tradeoff is the right one when the output feeds an
        LLM that will reason over bad context with confidence.
      </>
    ),
  },
  {
    anchor: "Faceted retrieval, constrained ranking",
    title: "Faceted retrieval under budget",
    body: (
      <>
        Borg doesn&apos;t bet everything on one ranked list. It retrieves
        across entities, facts, procedures, and snapshots, then applies
        memory-type weights per task and namespace. That makes context
        selection more robust when the real budget is not documents, but a few
        thousand tokens inside a model window.
      </>
    ),
  },
  {
    anchor: "Bitemporal data management",
    title: (
      <>
        Temporal consistency <em>through supersession</em>
      </>
    ),
    body: (
      <>
        Facts in Borg have a lifecycle. Not merely true or false — observed,
        current, superseded, or archived, with valid time and recording time.
        That prevents the classic memory failure where a system retrieves both
        &quot;Python 3.9&quot; and &quot;Python 3.12&quot; with no attempt to
        resolve which one still applies.
      </>
    ),
  },
  {
    anchor: "“Lost in the Middle” · resource-aware retrieval",
    title: "Namespace scoping & token budgets",
    body: (
      <>
        LLMs do worse when useful context is diluted by unrelated material.
        Borg scopes memory by namespace before retrieval, then applies
        configurable token budgets per namespace. Context is treated like a
        scarce runtime resource, not an infinite dump target.
      </>
    ),
  },
  {
    anchor: "Consistency over system sprawl",
    title: "PostgreSQL as the source of truth",
    body: (
      <>
        pgvector covers similarity search. Recursive CTEs cover graph
        traversal. ACID transactions keep mutations coherent. pgAudit
        preserves traceability. A separate vector database or graph store adds
        new consistency boundaries and new failure modes. Borg stays
        PostgreSQL-native to avoid an entire class of distributed-state bugs.
      </>
    ),
  },
];

export default function SciencePage() {
  return (
    <>
      <PageHero
        num="§ /science — a paper, disguised as a page"
        title={
          <>
            LLM memory is not
            <br />a <em>search</em> problem.
          </>
        }
        lede="It is a knowledge-compilation problem. Borg's architecture is not an aesthetic choice — it is a response to how memory fails in LLM systems, grounded in cognitive science, information retrieval, temporal data management, and database design."
        meta={[
          { label: "read", value: "12 min" },
          { label: "written", value: "apr 2026" },
          { label: "cites", value: "4 primary sources" },
        ]}
      />

      <div className="jump">
        <div className="wrap inner">
          <span className="label">§ jump to</span>
          <a href="#thesis">Thesis</a>
          <a href="#flawed">What fails</a>
          <a href="#principles">First principles</a>
          <a href="#measured">Measured</a>
          <a href="#compilation">Compilation</a>
        </div>
      </div>

      <section className="block" id="thesis">
        <div className="wrap">
          <div className="thesis">
            <p className="pull">
              LLMs are stateless inference engines. Every call starts from
              zero. The memory layer therefore has to do{" "}
              <em>more than retrieve text</em>. It has to produce a
              trustworthy, budgeted, task-appropriate artifact on demand — then
              defend every element inside it.
            </p>
          </div>
        </div>
      </section>

      <section className="block" id="flawed">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 01 — WHAT FAILS</div>
              <h2>
                Two approaches
                <br />
                <em>that don&apos;t hold up.</em>
              </h2>
            </div>
            <p className="sub">
              Both are popular. Both work fine on a demo. Both degrade sharply
              once conversations accumulate across weeks and teams.
            </p>
          </div>

          <div className="split">
            <div className="flaw">
              <span className="fail-tag">common failure</span>
              <h3>Naive RAG</h3>
              <p className="summary">Vector search over raw conversation logs.</p>
              <p>
                Conversation chunks are noisy, context-dependent, and often
                stale. A chunk that says &quot;we use Redis&quot; becomes
                actively harmful once the team moves to PostgreSQL. Without
                supersession, decay, or trust signals, retrieval becomes
                contamination — and the model sounds confident while being
                wrong.
              </p>
            </div>
            <div className="flaw">
              <span className="fail-tag">common failure</span>
              <h3>Summarization chains</h3>
              <p className="summary">Periodic summaries of summaries.</p>
              <p>
                Lossy compression compounds. After a few passes you&apos;re
                left with clean, generic prose that sounds helpful but has
                lost the specific facts, edge cases, and decision rationale
                that matter during real work. The system gets <em>more</em>{" "}
                fluent and <em>less</em> useful.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="principles">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 02 — FIRST PRINCIPLES</div>
              <h2>
                Six anchors,
                <br />
                <em>six decisions.</em>
              </h2>
            </div>
            <p className="sub">
              Each choice solves a specific failure mode. None are aesthetic.
            </p>
          </div>

          <div className="card" style={{ padding: "0 28px" }}>
            {PRINCIPLES.map((p, i) => (
              <div key={i} className="principle">
                <div className="anchor">
                  <b>Scientific anchor</b>
                  {p.anchor}
                </div>
                <div>
                  <h3>{p.title}</h3>
                  <p>{p.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="block" id="measured">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 03 — MEASURED</div>
              <h2>
                The thesis,
                <br />
                <em>on ten tasks.</em>
              </h2>
            </div>
            <p className="sub">
              Cloud-infrastructure engineering workloads. Three conditions.
              Same evaluator, same ground truth, reproducible seeds.
            </p>
          </div>

          <div className="measured">
            <div className="panel-main">
              <p
                style={{
                  color: "var(--ink-2)",
                  fontSize: 15,
                  lineHeight: 1.7,
                  margin: "0 0 16px",
                }}
              >
                Across 10 benchmark tasks, Borg-compiled context (C) achieved{" "}
                <b style={{ color: "var(--accent)" }}>10/10 task success</b>{" "}
                versus 8/10 for top-10 vector RAG (B) and 0/10 for no memory
                (A). Retrieval precision reached{" "}
                <b style={{ color: "var(--accent)" }}>91.3%</b>, with a{" "}
                <b style={{ color: "var(--accent)" }}>78% lower stale-fact rate</b>{" "}
                and 61% less irrelevant content than vector RAG. Knowledge
                coverage improved by 16% (90.8% vs 78.2%).
              </p>
              <p
                style={{
                  color: "var(--ink-3)",
                  fontSize: 13,
                  lineHeight: 1.7,
                  margin: 0,
                }}
              >
                The gain comes from <em>what is included</em>, not from using
                fewer tokens — context token counts are comparable between B
                and C (2,806 vs 3,026). Full methodology, per-task results,
                and seeds on the{" "}
                <a href="/benchmarks" style={{ color: "var(--accent)" }}>
                  benchmarks page
                </a>
                .
              </p>
            </div>
            <div className="bottom">
              <span className="kicker">§ bottom line</span>
              <p className="pull">
                The systems that win at AI memory will treat it as data
                engineering, not vector search with better marketing.
              </p>
              <p style={{ color: "var(--ink-3)", fontSize: 13, margin: 0 }}>
                Borg is built around that assumption from the start.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="compilation">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 04 — COMPILATION</div>
              <h2>
                Compilation,
                <br />
                <em>not search.</em>
              </h2>
            </div>
            <p className="sub">
              This is the architectural bet underneath the whole system. The
              compiler analogy is literal.
            </p>
          </div>

          <div className="card">
            <p>
              RAG treats memory as a search problem: query in, documents out.
              Borg treats memory as a compilation problem: messy source
              material flows through a sequence of extraction, validation,
              resolution, supersession, ranking, and formatting passes{" "}
              <em>before any context reaches a model.</em>
            </p>
            <p>
              Source code is redundant, inconsistent, and written for humans. A
              compiler turns it into a smaller, structured artifact machines
              can use. Conversations are the same — contradictory, local,
              emotional, full of dead ends. Borg&apos;s offline pipeline
              compiles them into memory that can be trusted enough to retrieve
              from.
            </p>
            <p>
              That is why the pipeline has multiple passes. Embeddings, entity
              extraction, three-pass resolution, fact extraction, supersession,
              serving-state updates, procedure extraction, and snapshots each
              preserve a guarantee you lose if you cut the step out. The cost
              of each is modest; the cost of their absence is not.
            </p>
          </div>
        </div>
      </section>

      <Crosslinks
        left={{
          kicker: "/architecture",
          href: "/architecture",
          title: (
            <>
              The runtime — <em>15 tables, one function.</em>
            </>
          ),
          body: "Topology, schema, API surface, and the decisions behind each constraint. Where the theory becomes code.",
        }}
        right={{
          kicker: "/features",
          href: "/features",
          title: (
            <>
              Features, <em>with tradeoffs.</em>
            </>
          ),
          body: "Each capability plus the decision it implies. How supersession, classification, and ranking actually run.",
        }}
      />
    </>
  );
}
