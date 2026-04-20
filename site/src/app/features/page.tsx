import { PageHero, Crosslinks } from "@/components/Section";

export default function FeaturesPage() {
  return (
    <>
      <PageHero
        num="§ /features — apache 2.0 · ships today"
        title={
          <>
            Every capability,
            <br />
            <em>with its tradeoff.</em>
          </>
        }
        lede="Not a feature checklist. Each item below names the decision it implies, the failure mode it prevents, and the cost it accepts."
        meta={[
          { label: "read", value: "8 min" },
          { label: "last updated", value: "apr 2026" },
          { label: "scope", value: "open-source release" },
        ]}
      />

      <div className="jump">
        <div className="wrap inner">
          <span className="label">§ jump to</span>
          <a href="#extraction">Extraction</a>
          <a href="#temporal">Temporal</a>
          <a href="#compilation">Compilation</a>
          <a href="#procedures">Procedures</a>
          <a href="#audit">Audit</a>
          <a href="#namespaces">Namespaces</a>
        </div>
      </div>

      <section className="block" id="extraction">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 01 — EXTRACTION</div>
              <h2>
                Knowledge graph,
                <br />
                <em>not text soup.</em>
              </h2>
            </div>
            <p className="sub">
              An LLM pipeline turns every episode into typed entities, temporal
              facts, and candidate procedures. No manual tagging. No
              &quot;vectorize and hope&quot;.
            </p>
          </div>

          <div className="split">
            <div className="card">
              <h3>Entity extraction</h3>
              <p>
                Each episode runs through <code>gpt-5-mini</code> with a
                constrained taxonomy: person, organization, project, service,
                technology, pattern, environment, document, metric, decision.
                Up to 10 entities per episode, each with known aliases.
              </p>
              <p>
                The model is told to use the most specific common name —
                &quot;Webhook Gateway&quot;, not &quot;event delivery system&quot;.
                Generic concepts are rejected: <em>authentication</em> is not
                an entity, but <em>Webhook Signature Validation Pattern</em> is.
              </p>
              <p style={{ color: "var(--ink-3)" }}>
                ↳ Keeps the graph mergeable. Collisions are not.
              </p>
            </div>

            <div className="card">
              <h3>Three-pass resolution</h3>
              <p>
                <em>Prefer fragmentation over collision.</em> Two records for
                the same thing can be merged with one UPDATE. Two things
                wrongly merged corrupt every fact on both.
              </p>
              <table className="etable" style={{ marginTop: 12 }}>
                <thead>
                  <tr>
                    <th>Pass</th>
                    <th>Method</th>
                    <th>Conf.</th>
                    <th>Condition</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="pred">1</td>
                    <td>Exact name + type + ns</td>
                    <td className="mono">1.00</td>
                    <td>case-insensitive</td>
                  </tr>
                  <tr>
                    <td className="pred">2</td>
                    <td>Alias match</td>
                    <td className="mono">0.95</td>
                    <td>single match only</td>
                  </tr>
                  <tr>
                    <td className="pred">3</td>
                    <td>Semantic (embedding)</td>
                    <td className="mono">&gt; 0.92</td>
                    <td>top-2 gap &gt; 0.03, else conflict</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="card" style={{ marginTop: 20 }}>
            <h3>
              Canonical predicate registry — <em>24 verbs, 4 categories</em>
            </h3>
            <p>
              The LLM sees the full predicate list and is told to use canonical
              ones. Non-canonical predicates are tracked with occurrence counts
              for promotion review.
            </p>
            <div className="split" style={{ marginTop: 16 }}>
              <div>
                <div className="kicker" style={{ color: "var(--accent)", marginBottom: 8 }}>
                  Structural
                </div>
                <p
                  className="mono"
                  style={{ color: "var(--ink-3)", fontSize: 12, lineHeight: 1.7 }}
                >
                  uses · used_by · contains · contained_in · depends_on ·
                  dependency_of · implements · implemented_by · integrates_with
                  · authored · authored_by · owns · owned_by
                </p>
              </div>
              <div>
                <div className="kicker" style={{ color: "var(--accent)", marginBottom: 8 }}>
                  Temporal / Decisional / Operational
                </div>
                <p
                  className="mono"
                  style={{ color: "var(--ink-3)", fontSize: 12, lineHeight: 1.7 }}
                >
                  replaced · replaced_by · decided · decided_by · deployed_to ·
                  hosts · manages · managed_by · configured_with · targets ·
                  blocks · blocked_by
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="temporal">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 02 — TEMPORAL</div>
              <h2>
                Facts are
                <br />
                <em>superseded,</em> not overwritten.
              </h2>
            </div>
            <p className="sub">
              Every fact carries <code>valid_from</code> and{" "}
              <code>valid_until</code>. A contradicting fact marks the old one
              superseded — never deleted. History survives forever, working
              memory doesn&apos;t.
            </p>
          </div>

          <div className="card">
            <h3>Supersession in SQL</h3>
            <pre>
              <span className="c">
                -- March 1: Customer Portal uses Semantic Kernel
              </span>
              {"\n"}
              fact_id: a1b2… | predicate: <span className="k">uses</span> |
              valid_until: NULL | status: observed{"\n\n"}
              <span className="c">
                -- March 10: same subject, new object → old fact superseded
              </span>
              {"\n"}
              fact_id: a1b2… | predicate: <span className="k">uses</span> |
              valid_until: 2026-03-10 | status: superseded{"\n"}
              fact_id: c3d4… | predicate: <span className="k">uses</span> |
              valid_until: NULL | status: observed
            </pre>
            <p style={{ marginTop: 16 }}>
              Seven evidence statuses track the lifecycle:{" "}
              <code>user_asserted</code> → <code>observed</code> →{" "}
              <code>extracted</code> → <code>inferred</code> →{" "}
              <code>promoted</code> → <code>deprecated</code> →{" "}
              <code>superseded</code>. User-asserted outranks LLM-extracted.
              Superseded is excluded from compilation, kept for compliance.
            </p>
          </div>
        </div>
      </section>

      <section className="block" id="compilation">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 03 — COMPILATION</div>
              <h2>
                Task-specific
                <br />
                <em>context packages.</em>
              </h2>
            </div>
            <p className="sub">
              Different tasks need different memory. The compiler classifies
              intent, retrieves across multiple strategies, and weights memory
              types per task.
            </p>
          </div>

          <div className="card">
            <h3>Dual-profile classification</h3>
            <p>
              Borg identifies a primary <em>and</em> optional secondary task
              class. If the confidence gap is &lt; 0.3, both profiles run
              retrieval — eliminating single-path classification failure.
            </p>
            <table className="etable" style={{ marginTop: 14 }}>
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Retrieval profile</th>
                  <th>Episodic</th>
                  <th>Semantic</th>
                  <th>Procedural</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="pred">debug</td>
                  <td>Graph + Episode Recall</td>
                  <td className="mono">1.0</td>
                  <td className="mono">0.7</td>
                  <td className="mono">0.8</td>
                </tr>
                <tr>
                  <td className="pred">architecture</td>
                  <td>Fact Lookup + Graph</td>
                  <td className="mono">0.5</td>
                  <td className="mono">1.0</td>
                  <td className="mono">0.3</td>
                </tr>
                <tr>
                  <td className="pred">compliance</td>
                  <td>Episode Recall + Facts</td>
                  <td className="mono">1.0</td>
                  <td className="mono">0.8</td>
                  <td className="mono" style={{ color: "var(--danger)" }}>
                    0.0
                  </td>
                </tr>
                <tr>
                  <td className="pred">writing</td>
                  <td>Fact Lookup</td>
                  <td className="mono">0.3</td>
                  <td className="mono">1.0</td>
                  <td className="mono">0.6</td>
                </tr>
                <tr>
                  <td className="pred">chat</td>
                  <td>Fact Lookup</td>
                  <td className="mono">0.4</td>
                  <td className="mono">1.0</td>
                  <td className="mono">0.3</td>
                </tr>
              </tbody>
            </table>
            <p style={{ marginTop: 14, color: "var(--ink-3)", fontSize: 13 }}>
              Weight 0.0 = hard exclude. Procedural memory is excluded from
              compliance — candidate patterns aren&apos;t authoritative enough
              for audit trails.
            </p>
          </div>

          <div className="card" style={{ marginTop: 20 }}>
            <h3>
              Four-dimension ranking — <em>no opaque composite.</em>
            </h3>
            <p>
              Every candidate is scored on four interpretable dimensions. All
              four land in the audit trace.
            </p>
            <table className="etable" style={{ marginTop: 14 }}>
              <thead>
                <tr>
                  <th>Dimension</th>
                  <th>Weight</th>
                  <th>How it works</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <b>Relevance</b>
                  </td>
                  <td className="mono">0.40</td>
                  <td>Vector similarity × memory-type weight modifier.</td>
                </tr>
                <tr>
                  <td>
                    <b>Recency</b>
                  </td>
                  <td className="mono">0.25</td>
                  <td>
                    Linear decay over 90 days from <code>occurred_at</code>.
                  </td>
                </tr>
                <tr>
                  <td>
                    <b>Stability</b>
                  </td>
                  <td className="mono">0.20</td>
                  <td>Evidence status score + salience, blended 70/30.</td>
                </tr>
                <tr>
                  <td>
                    <b>Provenance</b>
                  </td>
                  <td className="mono">0.15</td>
                  <td>
                    procedure_assist 0.9 · fact_lookup 0.8 · graph 0.7 · episode 0.6
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="split" style={{ marginTop: 20 }}>
            <div className="card">
              <h3>Two output formats</h3>
              <p>
                <b>Structured XML</b> for Claude, Claude Code, Copilot.
                Metadata lives on attributes the model can reason about.
              </p>
              <p>
                <b>Compact JSON</b> for GPT, Codex, local models. No tag
                overhead.
              </p>
              <p>
                Format is picked by <code>model</code> param, override
                available.
              </p>
            </div>
            <div className="card">
              <h3>Specific facts extraction</h3>
              <p>
                A dedicated pass pulls the details generic extraction loses:
                IPs, CLI invocations, resource names, port numbers, version
                strings, numeric counts. Stored as structured metadata on the
                episode, retrievable alongside facts and procedures.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="procedures">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 04 — PROCEDURES</div>
              <h2>
                Patterns earn trust
                <br />
                <em>through observation.</em>
              </h2>
            </div>
            <p className="sub">
              Each episode&apos;s procedure pass captures candidate workflows,
              decision rules, best practices, conventions, and troubleshooting
              patterns. They start weak and accumulate evidence.
            </p>
          </div>
          <div className="card">
            <p>
              Each procedure starts with <code>confidence = 0.3</code> and{" "}
              <code>evidence_status = extracted</code>. When the same pattern
              reappears, the record is merged: observation count +1, confidence
              recomputed as a weighted average, source episode appended.
            </p>
            <p>
              Procedures do <b>not</b> participate in compilation until
              promoted — which requires observation in <b>3+ distinct episodes</b> and{" "}
              <code>confidence ≥ 0.8</code>.
            </p>
            <p style={{ color: "var(--ink-3)" }}>
              Deliberately conservative. A pattern that appears once may be a
              one-off. One that appears in five conversations over two weeks is
              probably real practice.
            </p>
          </div>
        </div>
      </section>

      <section className="block" id="audit">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 05 — AUDIT</div>
              <h2>
                Every decision,
                <br />
                <em>traceable.</em>
              </h2>
            </div>
            <p className="sub">
              The audit log is the primary mechanism for improving retrieval
              quality. Every <code>borg_think</code> call writes a full trace;
              every extraction run logs its outcome.
            </p>
          </div>
          <div className="split">
            <div className="card">
              <h3>Per-compile trace</h3>
              <p>
                Classification (primary + secondary w/ confidences), retrieval
                profiles executed, candidates found / selected / rejected with
                per-item score breakdowns, rejection reasons, compiled token
                count, output format, per-stage latency.
              </p>
            </div>
            <div className="card">
              <h3>Per-episode trace</h3>
              <p>
                Entities extracted / resolved / new, facts extracted, custom
                predicates encountered, evidence strengths, procedures
                extracted / merged, and any errors. Everything joinable with{" "}
                <code>borg_audit_log</code>.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="block" id="namespaces">
        <div className="wrap">
          <div className="section-head">
            <div>
              <div className="num">§ 06 — NAMESPACES</div>
              <h2>
                Hard isolation,
                <br />
                <em>by default.</em>
              </h2>
            </div>
            <p className="sub">
              Every entity, fact, and episode belongs to exactly one namespace.
              No cross-namespace queries. Per-namespace token budgets.
              Cross-namespace is a future feature, not an accident.
            </p>
          </div>
          <div className="card">
            <p>
              If &quot;APIM&quot; appears in two projects it exists as{" "}
              <em>two</em> separate entity rows. The only way information
              crosses is an explicit merge. No config flag will relax the query
              boundary.
            </p>
            <table className="etable" style={{ marginTop: 12 }}>
              <thead>
                <tr>
                  <th>Setting</th>
                  <th>Default</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <b>Isolation mode</b>
                  </td>
                  <td className="mono">hard</td>
                  <td>Structural. Not a permission check.</td>
                </tr>
                <tr>
                  <td>
                    <b>Token budget</b>
                  </td>
                  <td className="mono">4 096 / ns</td>
                  <td>Compile trims to this ceiling.</td>
                </tr>
                <tr>
                  <td>
                    <b>Protected namespaces</b>
                  </td>
                  <td className="mono">default</td>
                  <td>Cannot be deleted.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <Crosslinks
        left={{
          kicker: "/architecture",
          href: "/architecture",
          title: (
            <>
              15 tables. <em>One schema.</em>
            </>
          ),
          body: "Reference layout, schema, API surface, deployment. Every table separates canonical data from serving state.",
        }}
        right={{
          kicker: "/science",
          href: "/science",
          title: (
            <>
              <em>Why</em> this works.
            </>
          ),
          body: "Grounded in Tulving, Fellegi-Sunter, bitemporal data, Lost-in-the-Middle. Memory isn't a search problem.",
        }}
      />
    </>
  );
}
