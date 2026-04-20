import { PageHero, Crosslinks } from "@/components/Section";

export default function DocsPage() {
  return (
    <>
      <PageHero
        num="§ /docs — mcp · rest · admin"
        title={
          <>
            The interaction surface,
            <br />
            <em>every endpoint.</em>
          </>
        }
        lede="Three MCP tools. A REST mirror for every one. A small set of admin endpoints for queues, snapshots, and traces. All open, none behind auth in the OSS release."
        meta={[
          { label: "transport", value: "MCP · streamable HTTP" },
          { label: "rest", value: "FastAPI · OpenAPI 3.1" },
          { label: "auth", value: "none · single-user" },
        ]}
      />

      <div className="jump">
        <div className="wrap inner">
          <span className="label">§ jump to</span>
          <a href="#mcp">MCP tools</a>
          <a href="#rest">REST mirror</a>
          <a href="#admin">Admin</a>
          <a href="#errors">Errors</a>
        </div>
      </div>

      <section className="block" id="mcp">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 01 — MCP TOOLS</div>
              <h2>
                Three tools,
                <br />
                <em>explicit schemas.</em>
              </h2>
            </div>
            <p className="sub">
              Every MCP client invokes these by name. All take JSON arguments
              matching the schema below.
            </p>
          </div>

          <div className="split" style={{ marginBottom: 20 }}>
            <div className="card">
              <h3>
                <code>borg_think</code> — <em>compile</em>
              </h3>
              <p>
                Classify the query, retrieve across strategies, rank on 4
                dimensions, compile a token-budgeted context package.
              </p>
              <pre>
                <span className="c">// arguments</span>
                {"\n"}
                &#123;{"\n"}
                {"  "}query: string,{"\n"}
                {"  "}namespace: string,{"\n"}
                {"  "}model?: &quot;claude&quot; | &quot;gpt&quot; | &quot;copilot&quot;,{"\n"}
                {"  "}task_hint?: &quot;debug&quot; | &quot;architecture&quot; | &quot;compliance&quot; | &quot;writing&quot; | &quot;chat&quot;,{"\n"}
                {"  "}budget_tokens?: number{"\n"}
                &#125;
              </pre>
            </div>

            <div className="card">
              <h3>
                <code>borg_learn</code> — <em>record</em>
              </h3>
              <p>
                Store an episode. Extraction runs async so this returns in
                milliseconds and never blocks the agent loop.
              </p>
              <pre>
                <span className="c">// arguments</span>
                {"\n"}
                &#123;{"\n"}
                {"  "}content: string,{"\n"}
                {"  "}source: &quot;claude-code&quot; | &quot;codex&quot; | &quot;copilot&quot; | &quot;kiro&quot; | &quot;slack&quot; | string,{"\n"}
                {"  "}namespace: string,{"\n"}
                {"  "}occurred_at?: ISO-8601,{"\n"}
                {"  "}participants?: string[]{"\n"}
                &#125;
              </pre>
            </div>
          </div>

          <div className="card">
            <h3>
              <code>borg_recall</code> — <em>browse</em>
            </h3>
            <p>
              Direct memory search without compilation. Raw episodes, facts,
              and procedures — for UI, audits, or the developer at the console.
            </p>
            <pre>
              <span className="c">// arguments</span>
              {"\n"}
              &#123;{"\n"}
              {"  "}query: string,{"\n"}
              {"  "}namespace: string,{"\n"}
              {"  "}memory_type?: &quot;episodic&quot; | &quot;semantic&quot; | &quot;procedural&quot; | &quot;all&quot;,{"\n"}
              {"  "}limit?: number{"\n"}
              &#125;
            </pre>
          </div>
        </div>
      </section>

      <section className="block" id="rest">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 02 — REST MIRROR</div>
              <h2>
                Same tools,
                <br />
                <em>plain HTTP.</em>
              </h2>
            </div>
            <p className="sub">
              Not every upstream speaks MCP. The REST mirror gives you the
              same surface for webhooks, CI, ad-hoc scripts, or legacy apps.
            </p>
          </div>

          <div className="card" style={{ padding: "0 28px" }}>
            <table className="etable">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Path</th>
                  <th>Maps to</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                    POST
                  </td>
                  <td className="mono">/api/think</td>
                  <td>
                    <code>borg_think</code>
                  </td>
                </tr>
                <tr>
                  <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                    POST
                  </td>
                  <td className="mono">/api/learn</td>
                  <td>
                    <code>borg_learn</code>
                  </td>
                </tr>
                <tr>
                  <td className="mono" style={{ color: "oklch(78% 0.14 210)" }}>
                    POST
                  </td>
                  <td className="mono">/api/recall</td>
                  <td>
                    <code>borg_recall</code>
                  </td>
                </tr>
                <tr>
                  <td className="mono" style={{ color: "var(--accent)" }}>
                    GET
                  </td>
                  <td className="mono">/health</td>
                  <td>Liveness · returns engine + worker status</td>
                </tr>
                <tr>
                  <td className="mono" style={{ color: "var(--accent)" }}>
                    GET
                  </td>
                  <td className="mono">/docs</td>
                  <td>Swagger UI · full OpenAPI spec</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="block" id="admin">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 03 — ADMIN</div>
              <h2>
                Inspect the pipeline,
                <br />
                <em>drive the worker.</em>
              </h2>
            </div>
            <p className="sub">
              The admin surface lets you observe the extraction queue, trigger
              snapshots, and audit exactly what went into the last compile.
            </p>
          </div>

          <div className="split">
            <div className="card">
              <h3>Observability</h3>
              <pre>
                <span className="c">// queue depth, running, errors, throughput</span>
                {"\n"}GET /api/admin/queue{"\n\n"}
                <span className="c">// list recent entities / facts / procedures</span>
                {"\n"}GET /api/admin/entities{"\n"}GET /api/admin/facts{"\n"}GET /api/admin/procedures
              </pre>
            </div>
            <div className="card">
              <h3>Control</h3>
              <pre>
                <span className="c">// force-process or requeue</span>
                {"\n"}POST /admin/process-episode{"\n"}POST /admin/requeue-failed{"\n\n"}
                <span className="c">// snapshot + cost</span>
                {"\n"}POST /admin/snapshot{"\n"}GET /admin/cost-summary
              </pre>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="errors">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 04 — ERRORS</div>
              <h2>
                Predictable failures,
                <br />
                <em>diagnostic bodies.</em>
              </h2>
            </div>
            <p className="sub">
              Everything returns JSON. Every 4xx and 5xx includes a{" "}
              <code>detail</code> field and, where applicable, a{" "}
              <code>hint</code> with the exact next step.
            </p>
          </div>
          <div className="card" style={{ padding: "0 28px" }}>
            <table className="etable">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Condition</th>
                  <th>Hint body</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="mono">400</td>
                  <td>Missing / malformed args</td>
                  <td style={{ color: "var(--ink-3)" }}>
                    Invalid field enumerated with a JSON pointer.
                  </td>
                </tr>
                <tr>
                  <td className="mono">404</td>
                  <td>Unknown namespace</td>
                  <td style={{ color: "var(--ink-3)" }}>
                    Lists known namespaces within reason.
                  </td>
                </tr>
                <tr>
                  <td className="mono">429</td>
                  <td>Rate-limited (default 60/min on learn)</td>
                  <td style={{ color: "var(--ink-3)" }}>
                    Retry after <code>Retry-After</code> seconds.
                  </td>
                </tr>
                <tr>
                  <td className="mono">503</td>
                  <td>Worker queue backed up &gt; 1 min</td>
                  <td style={{ color: "var(--ink-3)" }}>
                    Reads still served from last-good state.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <Crosslinks
        left={{
          kicker: "/integrations",
          href: "/integrations",
          title: (
            <>
              Any MCP client, <em>one memory.</em>
            </>
          ),
          body: "Claude Code, Codex, Copilot, Kiro — all four clients verified, configs shown.",
        }}
        right={{
          kicker: "/architecture",
          href: "/architecture",
          title: (
            <>
              15 tables. <em>One schema.</em>
            </>
          ),
          body: "How the endpoints above map to tables, functions, and the offline worker.",
        }}
      />
    </>
  );
}
