import { PageHero, Crosslinks } from "@/components/Section";

export default function IntegrationsPage() {
  return (
    <>
      <PageHero
        num="§ /integrations — claude code · codex · copilot · kiro"
        title={
          <>
            Any MCP client,
            <br />
            <em>one memory.</em>
          </>
        }
        lede="Point every agent at the same Borg. No per-client SDKs, no per-client memories — the graph is shared by the database, not by passing bytes around."
        meta={[
          { label: "transport", value: "MCP · streamable HTTP" },
          { label: "port", value: "8080/mcp" },
          { label: "clients", value: "4 verified · 1 soon" },
        ]}
      />

      <div className="jump">
        <div className="wrap inner">
          <span className="label">§ jump to</span>
          <a href="#overview">Overview</a>
          <a href="#install">Zero-SDK install</a>
          <a href="#clients">Client setup</a>
          <a href="#steering">Steering</a>
          <a href="#rest">REST fallback</a>
        </div>
      </div>

      <section className="block" id="overview">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 01 — OVERVIEW</div>
              <h2>
                One Postgres.
                <br />
                <em>Every client.</em>
              </h2>
            </div>
            <p className="sub">
              The OSS release runs as a single <code>borg-engine</code>{" "}
              listening on <code>:8080/mcp</code>. Every MCP client — Claude
              Code, Codex CLI, Copilot, Kiro — points at the same endpoint and
              reads from the same graph.
            </p>
          </div>

          <div className="split">
            <div className="card">
              <h3>No SDKs, no lock-in</h3>
              <p>
                The entire client surface is three MCP tools:{" "}
                <code>borg_think</code>, <code>borg_learn</code>,{" "}
                <code>borg_recall</code>. If your agent speaks MCP over
                streamable HTTP, it can use Borg unchanged.
              </p>
            </div>
            <div className="card">
              <h3>Share memory across tools</h3>
              <p>
                Claude Code writes. Codex reads. Copilot queries. One
                Postgres. No synchronization daemon, no cross-SDK pipeline —
                just a shared namespace on a shared engine.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="install">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 02 — ZERO-SDK INSTALL</div>
              <h2>
                Two commands.
                <br />
                <em>Everything wired.</em>
              </h2>
            </div>
            <p className="sub">
              <code>install.sh</code> detects Docker, starts the stack, writes
              your OpenAI key, and installs the <code>borg</code> CLI.{" "}
              <code>borg init</code> detects which tools you use and writes
              the right project config.
            </p>
          </div>
          <div className="card">
            <pre>
              <span className="c">
                # one command — brings up Postgres + borg-engine + CLI
              </span>
              {"\n"}curl -fsSL https://raw.githubusercontent.com/villanub/borgmemory/main/install.sh | sh{"\n\n"}
              <span className="c">
                # in any project — detects Claude / Copilot / Codex / Kiro
              </span>
              {"\n"}cd your-project{"\n"}borg init
            </pre>
          </div>
        </div>
      </section>

      <section className="block" id="clients">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 03 — CLIENT SETUP</div>
              <h2>
                Four verified clients,
                <br />
                <em>one config pattern.</em>
              </h2>
            </div>
            <p className="sub">
              Every client below is wired through <code>mcp-remote</code> for
              local MCP over HTTP. <code>borg init</code> generates these
              snippets for you; they&apos;re shown here for reference.
            </p>
          </div>

          <div className="split" style={{ marginBottom: 20 }}>
            <div className="client">
              <header>
                <span className="name">Claude Code</span>
                <span className="badge">verified</span>
              </header>
              <pre>
                <span className="c">// .mcp.json at project root</span>
                {"\n"}
                &#123;{"\n"}
                {"  "}&quot;mcpServers&quot;: &#123;{"\n"}
                {"    "}&quot;borg&quot;: &#123;{"\n"}
                {"      "}&quot;command&quot;: &quot;bash&quot;,{"\n"}
                {"      "}&quot;args&quot;: [&quot;-lc&quot;, &quot;exec npx -y mcp-remote http://localhost:8080/mcp 35535&quot;]{"\n"}
                {"    "}&#125;{"\n"}
                {"  "}&#125;{"\n"}
                &#125;
              </pre>
              <footer>
                Project instructions live in <code>CLAUDE.md</code>, generated
                by <code>borg init</code>.
              </footer>
            </div>

            <div className="client">
              <header>
                <span className="name">Codex CLI</span>
                <span className="badge">verified</span>
              </header>
              <pre>
                <span className="c"># ~/.codex/config.toml</span>
                {"\n"}
                [mcp_servers.borg]{"\n"}
                command = &quot;bash&quot;{"\n"}
                startup_timeout_sec = 30{"\n"}
                args = [{"\n"}
                {"  "}&quot;-lc&quot;,{"\n"}
                {"  "}&quot;exec npx -y mcp-remote http://localhost:8080/mcp 35534 --resource http://localhost:8080/mcp&quot;,{"\n"}
                ]
              </pre>
              <footer>
                Start a fresh Codex session after editing config and it will
                launch the Borg MCP process automatically.
              </footer>
            </div>
          </div>

          <div className="split">
            <div className="client">
              <header>
                <span className="name">Kiro CLI</span>
                <span className="badge">verified</span>
              </header>
              <pre>
                <span className="c">// ~/.kiro/settings/mcp.json</span>
                {"\n"}
                &#123;{"\n"}
                {"  "}&quot;mcpServers&quot;: &#123;{"\n"}
                {"    "}&quot;borg&quot;: &#123;{"\n"}
                {"      "}&quot;command&quot;: &quot;bash&quot;,{"\n"}
                {"      "}&quot;args&quot;: [&quot;-lc&quot;, &quot;exec npx -y mcp-remote http://localhost:8080/mcp 35536&quot;],{"\n"}
                {"      "}&quot;autoApprove&quot;: [&quot;borg_think&quot;, &quot;borg_learn&quot;, &quot;borg_recall&quot;]{"\n"}
                {"    "}&#125;{"\n"}
                {"  "}&#125;{"\n"}
                &#125;
              </pre>
              <footer>
                Kiro supports global and local MCP settings, per-agent{" "}
                <code>mcpServers</code>, plus steering files and richer hooks.
              </footer>
            </div>

            <div className="client">
              <header>
                <span className="name">GitHub Copilot</span>
                <span className="badge">verified</span>
              </header>
              <pre>
                <span className="c">// .vscode/mcp.json</span>
                {"\n"}
                &#123;{"\n"}
                {"  "}&quot;servers&quot;: &#123;{"\n"}
                {"    "}&quot;borg&quot;: &#123;{"\n"}
                {"      "}&quot;command&quot;: &quot;bash&quot;,{"\n"}
                {"      "}&quot;args&quot;: [&quot;-lc&quot;, &quot;exec npx -y mcp-remote http://localhost:8080/mcp 35537&quot;]{"\n"}
                {"    "}&#125;{"\n"}
                {"  "}&#125;{"\n"}
                &#125;
              </pre>
              <footer>
                Copilot reads MCP config from <code>.vscode/mcp.json</code>.
                Project instructions live in <code>copilot-instructions.md</code>.
              </footer>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="steering">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 04 — INSTRUCTIONS &amp; STEERING</div>
              <h2>
                Tell each client
                <br />
                <em>when to consult memory.</em>
              </h2>
            </div>
            <p className="sub">
              Memory is only useful if the agent calls for it. The hook +
              instruction matrix below keeps behavior consistent across tools.
            </p>
          </div>
          <div className="card" style={{ padding: "0 28px" }}>
            <table className="etable">
              <thead>
                <tr>
                  <th>Tool</th>
                  <th>Global instructions</th>
                  <th>Project instructions</th>
                  <th>Hooks</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th>
                    <b>Claude Code</b>
                  </th>
                  <td className="mono">~/.claude/CLAUDE.md</td>
                  <td className="mono">CLAUDE.md</td>
                  <td className="mono">PostSession</td>
                </tr>
                <tr>
                  <th>
                    <b>Codex CLI</b>
                  </th>
                  <td className="mono">~/.codex/AGENTS.md</td>
                  <td className="mono">AGENTS.md</td>
                  <td className="mono" style={{ color: "var(--ink-3)" }}>
                    none native
                  </td>
                </tr>
                <tr>
                  <th>
                    <b>Kiro CLI</b>
                  </th>
                  <td className="mono">~/.kiro/steering/AGENTS.md</td>
                  <td className="mono">AGENTS.md · .kiro/steering/*.md</td>
                  <td className="mono">stop · postToolUse · agentSpawn</td>
                </tr>
                <tr>
                  <th>
                    <b>GitHub Copilot</b>
                  </th>
                  <td className="mono" style={{ color: "var(--ink-3)" }}>
                    n/a
                  </td>
                  <td className="mono">copilot-instructions.md</td>
                  <td className="mono" style={{ color: "var(--ink-3)" }}>
                    none native
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="block" id="rest">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 05 — REST FALLBACK</div>
              <h2>
                Not an MCP client?
                <br />
                <em>Same tools over REST.</em>
              </h2>
            </div>
            <p className="sub">
              Every MCP tool has a REST mirror. Ingest episodes from webhooks,
              CI, or legacy apps with plain HTTP.
            </p>
          </div>
          <div className="split">
            <div className="card">
              <h3>Ingest an episode</h3>
              <pre>
                <span className="c">POST</span> /api/learn{"\n"}
                content-type: application/json{"\n\n"}
                &#123;{"\n"}
                {"  "}&quot;namespace&quot;: &quot;product-engineering&quot;,{"\n"}
                {"  "}&quot;content&quot;: &quot;We moved Customer Portal off Semantic Kernel to Azure AI Foundry on Mar 10.&quot;,{"\n"}
                {"  "}&quot;source&quot;: &quot;slack:#eng-arch&quot;,{"\n"}
                {"  "}&quot;occurred_at&quot;: &quot;2026-03-10T15:04:00Z&quot;{"\n"}
                &#125;
              </pre>
            </div>
            <div className="card">
              <h3>Compile context</h3>
              <pre>
                <span className="c">POST</span> /api/think{"\n"}
                content-type: application/json{"\n\n"}
                &#123;{"\n"}
                {"  "}&quot;namespace&quot;: &quot;product-engineering&quot;,{"\n"}
                {"  "}&quot;query&quot;: &quot;why did we move off Semantic Kernel?&quot;,{"\n"}
                {"  "}&quot;model&quot;: &quot;claude-sonnet-4.5&quot;,{"\n"}
                {"  "}&quot;task_hint&quot;: &quot;architecture&quot;{"\n"}
                &#125;
              </pre>
            </div>
          </div>
        </div>
      </section>

      <Crosslinks
        left={{
          kicker: "/docs",
          href: "/docs",
          title: (
            <>
              Full API reference. <em>Try it live.</em>
            </>
          ),
          body: "Every endpoint, every schema, every parameter. Open an interactive console against your local Borg.",
        }}
        right={{
          kicker: "/features",
          href: "/features",
          title: (
            <>
              Features, <em>with tradeoffs.</em>
            </>
          ),
          body: "Every capability plus the decision it implies. Fragmentation over collision. Supersession over overwrite.",
        }}
      />
    </>
  );
}
