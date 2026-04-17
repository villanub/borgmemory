import { Section } from "@/components/Section";

export default function Features() {
  return (
    <div className="pt-16">
      {/* Header */}
      <div className="border-b border-[var(--border)] bg-gradient-to-b from-[var(--accent-green)]/5 to-transparent">
        <div className="mx-auto max-w-6xl px-6 pb-12 pt-20">
          <h1 className="text-4xl font-extrabold text-[var(--text-primary)]">
            Features
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-[var(--text-secondary)]">
            Everything Borg does, how it works under the hood, and the trade-offs
            behind each decision.
          </p>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            Every feature below ships in the open source release under Apache 2.0.
          </p>
        </div>
      </div>

      {/* Knowledge Graph Extraction */}
      <Section
        id="extraction"
        title="Knowledge Graph Extraction"
        subtitle="An LLM pipeline that runs on every ingested episode. Extracts entities, facts, and procedures into a typed, temporal knowledge graph. No manual tagging."
      >
        <div className="space-y-8">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Entity Extraction
            </h3>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Each episode is processed by gpt-5-mini to extract up to 10 entities
              with a constrained type taxonomy: person, organization, project, service,
              technology, pattern, environment, document, metric, decision. The LLM is
              instructed to use the most specific common name ("Webhook Gateway" not
              "event delivery system") and to include known aliases.
            </p>
            <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
              Generic concepts are excluded — "authentication" is not an entity, but
              "Webhook Signature Validation Pattern" is. Actions and events are excluded. This
              constraint keeps the graph clean and mergeable.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Three-Pass Entity Resolution
            </h3>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)] mb-4">
              Design principle: <strong>prefer fragmentation over collision</strong>.
              Two separate entities for the same thing can be merged later with a
              simple UPDATE. Two different things incorrectly merged corrupt every fact
              attached to both. Fragmentation is recoverable. Collision is not.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Pass</th>
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Method</th>
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Confidence</th>
                    <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">Condition</th>
                  </tr>
                </thead>
                <tbody className="text-[var(--text-secondary)]">
                  <tr className="border-b border-[var(--border)]/50">
                    <td className="py-3 pr-6 text-[var(--accent-green)] font-mono">1</td>
                    <td className="py-3 pr-6">Exact match (name + type + namespace)</td>
                    <td className="py-3 pr-6">1.0</td>
                    <td className="py-3">Case-insensitive</td>
                  </tr>
                  <tr className="border-b border-[var(--border)]/50">
                    <td className="py-3 pr-6 text-[var(--accent-green)] font-mono">2</td>
                    <td className="py-3 pr-6">Alias match (properties→aliases)</td>
                    <td className="py-3 pr-6">0.95</td>
                    <td className="py-3">Single match only</td>
                  </tr>
                  <tr>
                    <td className="py-3 pr-6 text-[var(--accent-green)] font-mono">3</td>
                    <td className="py-3 pr-6">Semantic similarity (embedding)</td>
                    <td className="py-3 pr-6">&gt; 0.92</td>
                    <td className="py-3">Top-two gap &gt; 0.03, else flag as conflict</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="mt-4 text-sm text-[var(--text-muted)]">
              When ambiguous — the top two semantic candidates are within 0.03 of each
              other — a conflict record is created and a new entity is born. Conflicts
              are visible via the admin API for manual review.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Canonical Predicate Registry
            </h3>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)] mb-4">
              24 canonical predicates across four categories ensure consistent, queryable
              relationships. The LLM is given the full list and instructed to use canonical
              predicates where possible. Non-canonical predicates are flagged as custom
              and tracked with occurrence counts for promotion review.
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                { cat: "Structural", preds: "uses/used_by, contains/contained_in, depends_on/dependency_of, implements/implemented_by, integrates_with, authored/authored_by, owns/owned_by" },
                { cat: "Temporal", preds: "replaced/replaced_by" },
                { cat: "Decisional", preds: "decided/decided_by" },
                { cat: "Operational", preds: "deployed_to/hosts, manages/managed_by, configured_with, targets, blocked_by/blocks" },
              ].map((group) => (
                <div key={group.cat} className="rounded-lg border border-[var(--border)]/50 bg-[var(--bg-primary)] p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-green)] mb-2">
                    {group.cat}
                  </p>
                  <p className="text-xs leading-relaxed text-[var(--text-muted)] font-mono">
                    {group.preds}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* Temporal Facts */}
      <Section
        id="temporal-facts"
        title="Temporal Facts with Supersession"
        subtitle="Facts are not overwritten. They're superseded. The full history is always available."
        className="border-t border-[var(--border)]"
      >
        <div className="space-y-6">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Every fact carries <code>valid_from</code> and <code>valid_until</code> timestamps.
              When a new fact contradicts an existing current fact (same subject + predicate +
              different object), the old fact is marked <code>superseded</code> with
              <code>valid_until = now()</code>. The old fact is never deleted.
            </p>
            <pre className="mt-4 text-xs">
              <code>{`-- March 1: Customer Portal uses Semantic Kernel
fact_id: a1b2... | predicate: uses | valid_until: NULL | status: observed

-- March 10: Customer Portal uses Azure AI Foundry (new decision)
-- Old fact automatically superseded:
fact_id: a1b2... | predicate: uses | valid_until: 2026-03-10 | status: superseded
fact_id: c3d4... | predicate: uses | valid_until: NULL       | status: observed`}</code>
            </pre>
            <p className="mt-4 text-sm text-[var(--text-muted)]">
              Seven evidence statuses track the lifecycle of every fact:
              <code>user_asserted</code> → <code>observed</code> → <code>extracted</code> →
              <code>inferred</code> → <code>promoted</code> → <code>deprecated</code> →
              <code>superseded</code>. Authority hierarchy: user-asserted facts outrank
              LLM-extracted ones. Superseded facts are excluded from compilation but
              always available for compliance queries.
            </p>
          </div>
        </div>
      </Section>

      {/* Task-Specific Compilation */}
      <Section
        id="compilation"
        title="Task-Specific Context Compilation"
        subtitle="Different tasks need different memory. The compiler classifies intent, retrieves from multiple strategies, and weights memory types per task class."
        className="border-t border-[var(--border)]"
      >
        <div className="space-y-6">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Dual-Profile Classification
            </h3>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)] mb-4">
              Instead of mapping a query to one task class, Borg identifies a primary
              and optional secondary class. If the confidence gap between them is
              less than 0.3, both profiles execute retrieval. This eliminates the
              single-path classification failure mode.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="pb-3 pr-4 text-left font-semibold text-[var(--text-primary)]">Task</th>
                    <th className="pb-3 pr-4 text-left font-semibold text-[var(--text-primary)]">Retrieval Profiles</th>
                    <th className="pb-3 pr-4 text-left font-semibold text-[var(--text-primary)]">Episodic</th>
                    <th className="pb-3 pr-4 text-left font-semibold text-[var(--text-primary)]">Semantic</th>
                    <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">Procedural</th>
                  </tr>
                </thead>
                <tbody className="text-[var(--text-secondary)]">
                  {[
                    ["debug", "Graph + Episode Recall", "1.0", "0.7", "0.8"],
                    ["architecture", "Fact Lookup + Graph", "0.5", "1.0", "0.3"],
                    ["compliance", "Episode Recall + Facts", "1.0", "0.8", "0.0"],
                    ["writing", "Fact Lookup", "0.3", "1.0", "0.6"],
                    ["chat", "Fact Lookup", "0.4", "1.0", "0.3"],
                  ].map(([task, profiles, ep, sem, proc]) => (
                    <tr key={task} className="border-b border-[var(--border)]/50">
                      <td className="py-3 pr-4 font-mono text-[var(--accent-green)]">{task}</td>
                      <td className="py-3 pr-4">{profiles}</td>
                      <td className="py-3 pr-4 font-mono">{ep}</td>
                      <td className="py-3 pr-4 font-mono">{sem}</td>
                      <td className="py-3 font-mono">
                        {proc === "0.0" ? (
                          <span className="text-[var(--accent-red)]">{proc}</span>
                        ) : (
                          proc
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-4 text-sm text-[var(--text-muted)]">
              Weight 0.0 = hard exclude. Procedural memory is excluded from compliance
              tasks because candidate patterns are not authoritative enough for audit trails.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Four-Dimension Ranking
            </h3>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)] mb-4">
              Every candidate is scored on four interpretable dimensions. No opaque
              composite. All scores are logged in the audit trace.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Dimension</th>
                    <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Weight</th>
                    <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">How it works</th>
                  </tr>
                </thead>
                <tbody className="text-[var(--text-secondary)]">
                  <tr className="border-b border-[var(--border)]/50">
                    <td className="py-3 pr-6 font-semibold text-[var(--text-primary)]">Relevance</td>
                    <td className="py-3 pr-6 font-mono">0.40</td>
                    <td className="py-3">Vector similarity (when available), multiplied by memory-type weight modifier</td>
                  </tr>
                  <tr className="border-b border-[var(--border)]/50">
                    <td className="py-3 pr-6 font-semibold text-[var(--text-primary)]">Recency</td>
                    <td className="py-3 pr-6 font-mono">0.25</td>
                    <td className="py-3">Linear decay over 90 days from occurred_at</td>
                  </tr>
                  <tr className="border-b border-[var(--border)]/50">
                    <td className="py-3 pr-6 font-semibold text-[var(--text-primary)]">Stability</td>
                    <td className="py-3 pr-6 font-mono">0.20</td>
                    <td className="py-3">Evidence status score blended with fact_state.salience_score (70/30)</td>
                  </tr>
                  <tr>
                    <td className="py-3 pr-6 font-semibold text-[var(--text-primary)]">Provenance</td>
                    <td className="py-3 pr-6 font-mono">0.15</td>
                    <td className="py-3">Retrieval source quality (procedure_assist=0.9, fact_lookup=0.8, graph=0.7, episode=0.6)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Two Output Formats
            </h3>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              <strong>Structured XML</strong> for Claude, Claude Code, and Copilot.
              Tags carry metadata (evidence status, salience scores, dates) that models
              can reason about. <strong>Compact JSON</strong> for GPT, Codex CLI, and
              local models — minimal overhead, no tag parsing required. The model
              parameter on <code>borg_think</code> selects the format automatically,
              with a manual override available.
            </p>
          </div>
        </div>
      </Section>

      {/* Specific Facts Extraction */}
      <Section
        id="specific-facts"
        title="Specific Facts Extraction"
        subtitle="Named resources, IPs, CLI commands, and counts are stored as structured metadata on each episode."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            Beyond entity and fact extraction, the offline pipeline runs a dedicated
            specific-facts pass on each episode. It captures concrete, named details
            that general extraction tends to generalize away: IP addresses, CLI
            invocations, resource names, port numbers, version strings, and numeric
            counts. These are stored in episode metadata as structured key-value pairs.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
            Specific facts participate in retrieval like any other memory type. When
            a debug task asks about a particular error or command, the ranker can
            surface the original CLI invocation or IP address instead of a generic
            description.
          </p>
        </div>
      </Section>

      {/* Procedure Extraction */}
      <Section
        id="procedures"
        title="Procedure Extraction"
        subtitle="Borg identifies repeatable patterns, workflows, and decision rules from your conversations. Procedures earn trust through observation, not assertion."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            The extraction pipeline runs a dedicated LLM prompt to identify candidate
            procedures in each episode. Categories include workflow, decision_rule,
            best_practice, convention, and troubleshooting. Each procedure starts with
            a low confidence score (0.3) and evidence_status = "extracted".
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
            When the same pattern appears again, the existing record is merged:
            observation_count is incremented, confidence is recalculated as a weighted
            average, and the source episode is appended. Procedures are not used in
            compilation until promoted — which requires observation in 3+ distinct
            episodes and confidence ≥ 0.8.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
            This is deliberately conservative. A pattern that appears once might be a
            one-off. A pattern that appears in five conversations over two weeks is
            probably a real practice. The pipeline captures candidates early and lets
            evidence accumulate before surfacing them in context.
          </p>
        </div>
      </Section>

      {/* Audit & Observability */}
      <Section
        id="audit"
        title="Audit Log & Observability"
        subtitle="Every compilation decision is traceable. This is the primary mechanism for improving retrieval quality."
        className="border-t border-[var(--border)]"
      >
        <div className="space-y-6">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Every <code>borg_think</code> call writes a full trace to borg_audit_log:
              classification results (primary + secondary class with confidences), all
              retrieval profiles executed, candidates found/selected/rejected with
              per-item score breakdowns, rejection reasons, compiled token count, output
              format, and per-stage latency (classify, retrieve, rank, compile).
            </p>
            <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
              The offline worker logs extraction metrics for every episode processed:
              entities extracted/resolved/new, facts extracted, custom predicates
              encountered, evidence strengths, procedures extracted/merged, and any errors.
            </p>
          </div>
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Example dashboard queries
            </h3>
            <pre className="text-xs">
              <code>{`-- Retrieval precision over time
SELECT DATE(created_at),
       AVG(candidates_selected::float / NULLIF(candidates_found, 0)) as precision
FROM borg_audit_log WHERE task_class != 'extraction'
GROUP BY 1 ORDER BY 1;

-- Noise detection: most rejected items
SELECT item->>'id', item->>'reason', COUNT(*)
FROM borg_audit_log, jsonb_array_elements(rejected_items) item
WHERE task_class != 'extraction'
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 20;

-- Entity access hotspots
SELECT e.name, es.access_count, es.last_accessed, es.tier
FROM borg_entities e
JOIN borg_entity_state es ON es.entity_id = e.id
WHERE e.deleted_at IS NULL
ORDER BY es.access_count DESC LIMIT 20;`}</code>
            </pre>
          </div>
        </div>
      </Section>

      {/* Cost Tracking */}
      <Section
        id="cost-tracking"
        title="Cost Tracking"
        subtitle="Know what Borg costs before the invoice arrives."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            The admin API exposes <code>GET /api/admin/cost-summary</code>, which
            reports LLM token usage and estimated spend broken down by extraction,
            embedding, and compilation. The endpoint covers a configurable time window
            and groups costs by namespace. For a small team (~5 devs), expect roughly
            $15-30/month in LLM costs.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
            Supports both standard OpenAI and Azure OpenAI — pricing depends on
            which provider you configure.
          </p>
        </div>
      </Section>

      {/* Hybrid Episode Guarantee */}
      <Section
        id="hybrid-guarantee"
        title="Hybrid Episode Guarantee"
        subtitle="Ranking never discards all episodic evidence."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            The ranker enforces a minimum of 3 episodes in every compiled context
            package. If the scored ranking would drop all episodic candidates in
            favor of higher-scoring facts or procedures, the guarantee forces the
            top 3 episodes back into the output. This prevents the failure mode
            where compilation returns only abstract facts with no grounding evidence.
          </p>
        </div>
      </Section>

      {/* Namespace Isolation */}
      <Section
        id="namespaces"
        title="Namespace Isolation"
        subtitle="Hard isolation by default. Intentionally restrictive."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            Every entity, fact, episode, and procedure belongs to exactly one
            namespace. All queries are scoped to one namespace. Cross-namespace
            retrieval is not supported. If the same real-world entity ("APIM")
            appears in two projects, it exists as two separate entity records. Hot-tier
            content is namespace-scoped. There is no global hot tier.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
            Namespaces are managed via full CRUD endpoints at <code>/api/namespaces</code>.
            Each namespace has configurable <code>hot_tier_budget</code> (default 500 tokens)
            and <code>warm_tier_budget</code> (default 3000 tokens). The compiler reads
            these budgets at query time.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
            This is restrictive by design. Cross-namespace features can be added later
            with explicit design, not as an accident of unscoped queries.
          </p>
        </div>
      </Section>

      {/* Hot/Warm Tiers */}
      <Section
        id="tiers"
        title="Memory Tiers"
        subtitle="Hot memory is always injected. Warm memory is retrieved per-query. Cold tier is deferred."
        className="border-t border-[var(--border)]"
      >
        <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Tier</th>
                <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Behavior</th>
                <th className="pb-3 pr-6 text-left font-semibold text-[var(--text-primary)]">Promotion</th>
                <th className="pb-3 text-left font-semibold text-[var(--text-primary)]">Demotion</th>
              </tr>
            </thead>
            <tbody className="text-[var(--text-secondary)]">
              <tr className="border-b border-[var(--border)]/50">
                <td className="py-3 pr-6 font-semibold text-[var(--accent-green)]">Hot</td>
                <td className="py-3 pr-6">Always injected. ~500 token budget.</td>
                <td className="py-3 pr-6">Pinned by user, OR 5+ compilations in 14 days</td>
                <td className="py-3">Unpinned, OR not retrieved in 30 days, OR superseded</td>
              </tr>
              <tr>
                <td className="py-3 pr-6 font-semibold text-[var(--accent-amber)]">Warm</td>
                <td className="py-3 pr-6">Retrieved per-query. Default tier.</td>
                <td className="py-3 pr-6">Default state for all new memory</td>
                <td className="py-3">Superseded → archived. 90 days no access → archived.</td>
              </tr>
            </tbody>
          </table>
          <div className="mt-4 space-y-1">
            <p className="text-xs text-[var(--text-muted)]">• New facts always start warm. Never hot by default.</p>
            <p className="text-xs text-[var(--text-muted)]">• Superseded facts cannot be hot.</p>
            <p className="text-xs text-[var(--text-muted)]">• Procedures cannot be hot until ≥3 episodes, ≥7 days, confidence ≥0.8.</p>
            <p className="text-xs text-[var(--text-muted)]">• Hot tier overflow demotes lowest-salience item.</p>
          </div>
        </div>
      </Section>

      {/* PostgreSQL Maximalism */}
      <Section
        id="postgresql"
        title="Why PostgreSQL Only"
        subtitle="One database. No sync. No drift."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            Borg uses PostgreSQL for everything: relational data, vector search
            (pgvector), graph traversal (recursive CTEs), audit logging (pgAudit),
            and compliance. There is no external graph database. There is no separate
            vector store.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
            The advantage is consistency. Delete a fact, and the embedding, the graph
            edges, and the audit trail all update in one transaction. There is no sync
            to drift. The MCP server calls stored procedures and passes back results.
            All the heavy lifting — scoring, graph traversal, hybrid retrieval — runs
            inside the database.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
            The trade-off is real: at very high scale, a dedicated graph database or
            vector store would likely outperform recursive CTEs and pgvector HNSW
            indexes. That's a future escape hatch, introduced only if a measured
            bottleneck appears first. For the expected volume (hundreds of entities,
            thousands of facts), PostgreSQL is the right call.
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
            15 tables + 1 function. Runs on any PostgreSQL 14+ instance.
          </p>
        </div>
      </Section>
    </div>
  );
}
