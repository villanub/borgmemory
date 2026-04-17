import Link from "next/link";
import { Section } from "@/components/Section";

export default function Integrations() {
  return (
    <div className="pt-16">
      <div className="border-b border-[var(--border)] bg-gradient-to-b from-[var(--accent-blue)]/5 to-transparent">
        <div className="mx-auto max-w-6xl px-6 pb-12 pt-20">
          <h1 className="text-4xl font-extrabold text-[var(--text-primary)]">
            Integrations
          </h1>
          <p className="mt-4 max-w-3xl text-lg text-[var(--text-secondary)]">
            Connect Borg to MCP-capable clients, configure client instructions,
            and keep memory behavior consistent across tools.
          </p>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            MCP, AGENTS.md, steering files, hooks, and REST ingestion.
          </p>
        </div>
      </div>

      <Section
        id="overview"
        title="How Borg Integrates"
        subtitle="One MCP endpoint, four tools, and a small amount of client-specific setup."
      >
        <div className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Borg exposes a Streamable HTTP MCP server at <code>/mcp</code>. The
              surface is intentionally narrow: <code>borg_think</code> for context
              compilation, <code>borg_learn</code> for capture, <code>borg_recall</code>
              for direct lookup, and <code>borg_get_episode</code> for opening a
              full stored episode after recall. The OSS release runs locally with
              no authentication required.
            </p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ["borg_think", "Compile context before complex work."],
                ["borg_learn", "Record decisions and discoveries for later reuse."],
                ["borg_recall", "Search raw memory when you want direct evidence."],
                ["borg_get_episode", "Fetch one full episode by ID after browsing previews."],
              ].map(([name, desc]) => (
                <div
                  key={name}
                  className="rounded-lg border border-[var(--border)]/60 bg-[var(--bg-primary)] p-4"
                >
                  <code className="text-sm font-semibold text-[var(--accent-green)]">{name}</code>
                  <p className="mt-2 text-xs leading-relaxed text-[var(--text-muted)]">{desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              Generic Use Cases
            </h2>
            <div className="mt-4 space-y-4 text-sm text-[var(--text-secondary)]">
              <div>
                <p className="font-medium text-[var(--text-primary)]">Engineering</p>
                <p className="mt-1 text-[var(--text-muted)]">
                  Ask Borg what changed, how a bug was fixed, or which assumptions still hold before editing a risky path.
                </p>
              </div>
              <div>
                <p className="font-medium text-[var(--text-primary)]">Operations</p>
                <p className="mt-1 text-[var(--text-muted)]">
                  Capture incident notes, runbooks, release decisions, and environment policies so the next operator starts with context.
                </p>
              </div>
              <div>
                <p className="font-medium text-[var(--text-primary)]">Product and Support</p>
                <p className="mt-1 text-[var(--text-muted)]">
                  Recall feature requests, customer commitments, positioning notes, and prior decisions without repeating the same history.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Section>

      <Section
        id="zero-sdk"
        title="Zero-SDK Ingestion"
        subtitle="Install once, then borg init adds memory to any project without touching your code."
        className="border-t border-[var(--border)]"
      >
        <div className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Borg ships a CLI installer. Run the one-liner to install, then run{" "}
              <code>borg init</code> in any project directory. The init command
              writes the MCP configuration and generates agent-hook templates
              for every supported client: <code>CLAUDE.md</code>, <code>AGENTS.md</code>,
              <code>kiro.md</code>, and <code>copilot-instructions.md</code>. No
              SDK imports, no code changes, no new dependencies in your project.
              The next Claude Code, Codex, Kiro, or Copilot session in that
              directory will have Borg available automatically.
            </p>
            <div className="mt-5 overflow-hidden rounded-lg border border-[var(--border)]">
              <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-2">
                <span className="text-xs text-[var(--text-muted)]">Install and initialize</span>
              </div>
              <pre className="!border-0 !rounded-none !m-0 px-4 py-3 text-sm leading-7">
                <code>{`# Install the Borg CLI
curl -fsSL https://raw.githubusercontent.com/villanub/borgmemory/main/install.sh | sh

# Initialize Borg in your project
cd your-project
borg init

# Optional: cold-start from existing docs
borg bootstrap --dir ./docs --namespace my-project`}</code>
              </pre>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              What borg init does
            </h2>
            <div className="mt-4 space-y-4 text-sm text-[var(--text-secondary)]">
              <div>
                <p className="font-medium text-[var(--text-primary)]">MCP configuration</p>
                <p className="mt-1 text-[var(--text-muted)]">
                  Writes or updates the client-specific MCP config so Claude Code, Codex,
                  and Kiro can connect to Borg immediately.
                </p>
              </div>
              <div>
                <p className="font-medium text-[var(--text-primary)]">Agent-hook templates</p>
                <p className="mt-1 text-[var(--text-muted)]">
                  Generates <code>CLAUDE.md</code>, <code>AGENTS.md</code>,{" "}
                  <code>kiro.md</code>, and <code>copilot-instructions.md</code> with
                  Borg usage instructions so every AI client knows when to call{" "}
                  <code>borg_think</code> and <code>borg_learn</code>.
                </p>
              </div>
              <div>
                <p className="font-medium text-[var(--text-primary)]">Namespace detection</p>
                <p className="mt-1 text-[var(--text-muted)]">
                  Derives a project namespace from the directory name or git remote so
                  memory stays isolated per project from the first session.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Section>

      <Section
        id="clients"
        title="Client Setup"
        subtitle="Use the client-native MCP configuration where possible. borg init handles this automatically — manual steps are here for reference."
        className="border-t border-[var(--border)]"
      >
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              Claude Code
            </p>
            <pre className="mt-3 text-xs">
              <code>{`{
  "mcpServers": {
    "borg": {
      "command": "bash",
      "args": [
        "-lc",
        "export MCP_REMOTE_CONFIG_DIR=~/.mcp-auth/claude-borg && exec npx -y mcp-remote@0.1.28 http://localhost:8080/mcp 35535"
      ]
    }
  }
}`}</code>
            </pre>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              Claude Code works with Borg through <code>mcp-remote@0.1.28</code>, which handles FastMCP 3 OAuth discovery and the browser sign-in flow.
              Keep your project instructions in <code>CLAUDE.md</code>.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              Codex CLI
            </p>
            <pre className="mt-3 text-xs">
              <code>{`# ~/.codex/config.toml
mcp_oauth_credentials_store = "keyring"

[mcp_servers.borg]
command = "bash"
startup_timeout_sec = 30
args = [
  "-lc",
  "export MCP_REMOTE_CONFIG_DIR=~/.mcp-auth/codex-borg && exec npx -y mcp-remote http://localhost:8080/mcp 35534 --resource http://localhost:8080/mcp",
]`}</code>
            </pre>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              Codex CLI works cleanly through <code>mcp-remote</code> with its own
              auth cache directory and callback port. Start a fresh Codex session
              after adding the config and Codex will launch the Borg MCP process
              and complete the browser sign-in flow automatically.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              Kiro CLI
            </p>
            <pre className="mt-3 text-xs">
              <code>{`// ~/.kiro/settings/mcp.json
{
  "mcpServers": {
    "borg": {
      "command": "bash",
      "args": [
        "-lc",
        "export MCP_REMOTE_CONFIG_DIR=~/.mcp-auth/kiro-borg && exec npx -y mcp-remote@0.1.28 http://localhost:8080/mcp 35536"
      ],
      "autoApprove": [
        "borg_think",
        "borg_learn",
        "borg_recall",
        "borg_get_episode"
      ]
    }
  }
}`}</code>
            </pre>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              Kiro supports global and local MCP settings, per-agent <code>mcpServers</code>,
              plus steering files and richer hooks. The verified setup uses <code>mcp-remote@0.1.28</code> directly so Kiro can complete Borg&apos;s OAuth flow in the browser.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              GitHub Copilot
            </p>
            <pre className="mt-3 text-xs">
              <code>{`// .vscode/mcp.json
{
  "servers": {
    "borg": {
      "command": "bash",
      "args": [
        "-lc",
        "export MCP_REMOTE_CONFIG_DIR=~/.mcp-auth/copilot-borg && exec npx -y mcp-remote@0.1.28 http://localhost:8080/mcp 35537"
      ]
    }
  }
}`}</code>
            </pre>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              Copilot reads MCP server config from <code>.vscode/mcp.json</code>.
              Keep project instructions in <code>copilot-instructions.md</code> (generated
              by <code>borg init</code>).
            </p>
          </div>
        </div>
      </Section>

      <Section
        id="instructions"
        title="Instructions and Steering"
        subtitle="Tell each client when Borg should be consulted and when new knowledge should be captured."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="pb-3 pr-4 text-left font-semibold text-[var(--text-primary)]">Tool</th>
                  <th className="pb-3 pr-4 text-left font-semibold text-[var(--text-primary)]">Global instructions</th>
                  <th className="pb-3 pr-4 text-left font-semibold text-[var(--text-primary)]">Project instructions</th>
                  <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">Hooks</th>
                </tr>
              </thead>
              <tbody className="text-[var(--text-secondary)]">
                {[
                  ["Claude Code", "~/.claude/CLAUDE.md", "CLAUDE.md", "PostSession"],
                  ["Codex CLI", "~/.codex/AGENTS.md", "AGENTS.md", "None native"],
                  ["Kiro CLI", "~/.kiro/steering/AGENTS.md", "AGENTS.md or .kiro/steering/*.md", "stop, postToolUse, agentSpawn"],
                  ["GitHub Copilot", "N/A", "copilot-instructions.md", "None native"],
                  ["Claude Desktop", "Project system prompt (UI)", "Project system prompt (UI)", "None"],
                ].map(([tool, globalFile, projectFile, hooks]) => (
                  <tr key={tool} className="border-b border-[var(--border)]/50">
                    <td className="py-3 pr-4 font-medium text-[var(--text-primary)]">{tool}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{globalFile}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{projectFile}</td>
                    <td className="py-3 text-xs">{hooks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              Global guidance
            </p>
            <pre className="mt-3 text-xs">
              <code>{`## Borg Memory System
Call borg_think before complex tasks to retrieve professional context.
Call borg_learn after significant decisions or discoveries.
Call borg_recall when you want raw memory or direct evidence.
Use namespace "plurality" for Multi-Tool work coordination, "borg" for Borg dev, "default" for general.`}</code>
            </pre>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              Put the same block in each client&apos;s global instruction file so Borg is available even outside a project folder.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              Borg repo override
            </p>
            <pre className="mt-3 text-xs">
              <code>{`## Borg Namespace

For this repository, use Borg namespace "borg".

Always pass namespace="borg" to:
- borg_think
- borg_learn
- borg_recall

Do not omit the namespace.
Do not use "default" for work in this repository.`}</code>
            </pre>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              Use a project instruction file to pin the exact namespace for one repository. In this repo, add this block to <code>CLAUDE.md</code> or <code>AGENTS.md</code>.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              Kiro steering
            </p>
            <pre className="mt-3 text-xs">
              <code>{`# Global
~/.kiro/steering/AGENTS.md
~/.kiro/steering/*.md

# Per-project
AGENTS.md
.kiro/steering/*.md`}</code>
            </pre>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              Use <code>AGENTS.md</code> for cross-tool behavior and Kiro steering files when you want Kiro-specific guidance.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              Claude Desktop project instructions
            </p>
            <pre className="mt-3 text-xs">
              <code>{`# Project Settings → Instructions
## Borg Memory System
Call borg_think before complex tasks to retrieve professional context.
Call borg_learn after significant decisions or discoveries.
Call borg_recall when you want raw memory or direct evidence.

When to call borg_think:
- Starting work on any topic you haven't seen context for
- Debugging, architecture, compliance, or writing tasks
- When asked about prior decisions or project history

When to call borg_learn:
- A significant decision is made
- A bug is diagnosed and fixed
- A new pattern or convention is established
- Important context that should persist across sessions

Always use namespace "plurality" for Multi-Tool work coordination,
"borg" for Borg development, "default" for general knowledge.`}</code>
            </pre>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
              Manual ingestion
            </p>
            <pre className="mt-3 text-xs">
              <code>{`1. Open /docs
2. Click Authorize and complete Entra sign-in
3. Run POST /api/learn with:

{
  "content": "Decided to add a release-readiness checklist before production deploys...",
  "source": "manual",
  "namespace": "product-engineering"
}`}</code>
            </pre>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              REST remains useful for scripts, manual capture, and recovery workflows. Use the live docs OAuth flow instead of pasting tokens into client config. This assumes backend docs are enabled with <code>BORG_ENABLE_DOCS=true</code>.
            </p>
          </div>
        </div>
      </Section>

      <Section
        id="operational-notes"
        title="Operational Notes"
        subtitle="A few integration details matter in practice."
        className="border-t border-[var(--border)]"
      >
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)]">
              Authentication
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)]">
              The OSS release runs locally with no authentication — all requests
              pass through to the local Borg process. The <code>mcp-remote</code>
              wrappers shown above forward MCP traffic from each client to the
              local server; give each client its own callback port and auth cache
              directory so sessions don&apos;t collide.
            </p>
          </div>
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)]">
              Graceful degradation
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)]">
              If Azure OpenAI extraction settings are missing, Borg can still ingest episodes and keep them searchable by recency. When extraction becomes available again, failed items can be requeued through the admin API.
            </p>
          </div>
        </div>

        <div className="mt-8">
          <Link
            href="/docs"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--border-accent)] px-5 py-3 text-sm font-semibold text-[var(--text-primary)] transition-all hover:border-[var(--accent-green)]/50 hover:bg-[var(--bg-card)]"
          >
            Open Live API Docs
          </Link>
        </div>
      </Section>
    </div>
  );
}
