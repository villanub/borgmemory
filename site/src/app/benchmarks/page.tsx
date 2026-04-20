import { PageHero, Crosslinks } from "@/components/Section";
import { BenchBars } from "@/components/BenchBars";

const TASKS: [string, string, string, string][] = [
  ["1", "Diagnose API gateway 502 errors", "debug", "Prior auth failures, gateway error patterns, retry behavior"],
  ["2", "Event bus remediation architecture", "architecture", "Event bus topology, remediation decisions, integration patterns"],
  ["3", "Event-sync scoping decision", "compliance", "Scoping episodes, approval decisions, change boundaries"],
  ["4", "Agent query service purpose and architecture", "writing", "Agent query design, service purpose, architectural context"],
  ["5", "Trace message bus unauthorized errors", "debug", "Auth error episodes, token acquisition patterns, message bus facts"],
  ["6", "MCP gateway authentication architecture", "architecture", "Auth system entities, token flow facts, integration boundaries"],
  ["7", "Event bus token acquisition change rationale", "debug", "Token acquisition episodes, change rationale, prior decisions"],
  ["8", "Platform app CI security audit fix", "compliance", "CI audit episodes, security findings, remediation decisions"],
  ["9", "MCP gateway debugging pattern", "debug", "Debug procedure patterns, error resolution history, replay steps"],
  ["10", "Bulk event bus remediation architecture", "architecture", "Bulk remediation design, event bus entities, deployment facts"],
];

export default function BenchmarksPage() {
  return (
    <>
      <PageHero
        num="§ /benchmarks — 10 tasks · 3 conditions · apr 2026"
        title={
          <>
            Ten tasks.
            <br />
            <em>Three conditions.</em>
          </>
        }
        lede="Real production episodes from cloud-infrastructure engineering — incident response, schema migration, architecture review. Same evaluator model, same ground-truth labels across all three conditions."
        meta={[
          { label: "tasks", value: "10" },
          { label: "conditions", value: "A · B · C" },
          { label: "seeds", value: "in /bench" },
        ]}
      />

      <div className="jump">
        <div className="wrap inner">
          <span className="label">§ jump to</span>
          <a href="#results">Results</a>
          <a href="#method">Methodology</a>
          <a href="#tasks">Tasks</a>
          <a href="#caveats">Honest caveats</a>
        </div>
      </div>

      <section className="block" id="results">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 01 — RESULTS</div>
              <h2>
                Three conditions,
                <br />
                <em>head to head.</em>
              </h2>
            </div>
            <p className="sub">
              Bars fill as you scroll into view. C (Borg-compiled) achieves
              10/10 task success versus 8/10 for top-10 vector RAG (B) and
              0/10 for no memory (A).
            </p>
          </div>
          <BenchBars />
        </div>
      </section>

      <section className="block" id="method">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 02 — METHODOLOGY</div>
              <h2>
                How each condition
                <br />
                <em>actually runs.</em>
              </h2>
            </div>
            <p className="sub">
              All three conditions answer the same 10 tasks with the same
              model, scored by the same grader, against the same ground-truth
              labels.
            </p>
          </div>

          <div className="split-3">
            <div className="card">
              <div className="kicker" style={{ color: "var(--ink-3)", marginBottom: 8 }}>
                Condition A
              </div>
              <h3>No memory</h3>
              <p>
                The model answers each task with only the task prompt. No
                prior-session context. Baseline.
              </p>
            </div>
            <div className="card">
              <div className="kicker" style={{ color: "var(--ink-3)", marginBottom: 8 }}>
                Condition B
              </div>
              <h3>Top-10 vector RAG</h3>
              <p>
                Conversation logs are chunked, embedded with the same model as
                C, and the top-10 similar chunks are prepended verbatim to
                every task prompt.
              </p>
            </div>
            <div className="card">
              <div className="kicker" style={{ color: "var(--accent)", marginBottom: 8 }}>
                Condition C
              </div>
              <h3>Borg · compiled</h3>
              <p>
                Full pipeline: classify intent, retrieve across facts /
                episodes / graph, rank on 4 dimensions, compile a
                token-budgeted package. Output is injected, not matches.
              </p>
            </div>
          </div>

          <div className="card" style={{ marginTop: 20 }}>
            <h3>Metrics we measure</h3>
            <table className="etable" style={{ marginTop: 8 }}>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>What it means</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <b>Task success</b>
                  </td>
                  <td>
                    Binary — does the final answer cover every element the
                    grader labeled as required?
                  </td>
                </tr>
                <tr>
                  <td>
                    <b>Retrieval precision</b>
                  </td>
                  <td>
                    Of the items injected into context, what share were
                    actually used in the final answer?
                  </td>
                </tr>
                <tr>
                  <td>
                    <b>Stale-fact rate</b>
                  </td>
                  <td>
                    Fraction of facts in compiled context that have been
                    superseded or deprecated at the time of the query.
                  </td>
                </tr>
                <tr>
                  <td>
                    <b>Irrelevant rate</b>
                  </td>
                  <td>
                    Share of injected context that the grader marks as
                    off-topic for the task.
                  </td>
                </tr>
                <tr>
                  <td>
                    <b>Knowledge coverage</b>
                  </td>
                  <td>
                    Fraction of ground-truth facts that appeared in the
                    compiled context package.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="block" id="tasks">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 03 — TASKS</div>
              <h2>
                The ten prompts,
                <br />
                <em>and what memory they exercise.</em>
              </h2>
            </div>
            <p className="sub">
              Drawn from real engineering workloads, generalized for public
              benchmarks. Full seeds and prompts live in{" "}
              <code>bench/tasks.json</code> in the repo.
            </p>
          </div>

          <div className="card" style={{ padding: "0 28px" }}>
            <table className="etable">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Task</th>
                  <th>Type</th>
                  <th>Expected memory</th>
                </tr>
              </thead>
              <tbody>
                {TASKS.map(([n, t, type, mem]) => (
                  <tr key={n}>
                    <td className="pred">{n}</td>
                    <td>{t}</td>
                    <td>
                      <span className="tag">{type}</span>
                    </td>
                    <td style={{ color: "var(--ink-3)" }}>{mem}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="block" id="caveats">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 04 — HONEST CAVEATS</div>
              <h2>
                What this bench
                <br />
                <em>does not prove.</em>
              </h2>
            </div>
            <p className="sub">
              Every benchmark has edges. Here are ours, stated plainly so you
              can weigh them.
            </p>
          </div>

          <div className="card">
            <ul
              style={{
                margin: 0,
                paddingLeft: 20,
                color: "var(--ink-2)",
                fontSize: 14.5,
                lineHeight: 1.75,
              }}
            >
              <li>
                Self-reported results from a single evaluator model on a single
                domain (cloud-infrastructure / platform engineering). Not
                externally reproduced.
              </li>
              <li>
                10 tasks is a small N. Confidence intervals are wide; treat
                absolute numbers as directional, not definitive.
              </li>
              <li>
                Same LLM family used for task answering and grading — risks
                circularity. An independent judge model would strengthen the
                claim.
              </li>
              <li>
                Full per-task inputs, outputs, and grader reasoning live in{" "}
                <code>bench/results/report.md</code> on GitHub for audit.
              </li>
            </ul>
          </div>
        </div>
      </section>

      <Crosslinks
        left={{
          kicker: "/science",
          href: "/science",
          title: (
            <>
              <em>Why</em> this works.
            </>
          ),
          body: "Grounded in Tulving, Fellegi-Sunter, bitemporal data, Lost-in-the-Middle. The theory behind the numbers.",
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
