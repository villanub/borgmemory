import Link from "next/link";
import { Section } from "@/components/Section";

const flawedApproaches = [
  {
    title: "Naive RAG",
    summary: "Vector search over raw conversation logs.",
    whyItFails:
      "Conversation chunks are noisy, context-dependent, and often stale. A chunk that says \"we use Redis\" becomes actively harmful after the team has moved to PostgreSQL. Without supersession, decay, or trust, retrieval becomes contamination.",
  },
  {
    title: "Summarization Chains",
    summary: "Periodic summaries that get summarized again.",
    whyItFails:
      "Lossy compression compounds. After a few passes you are left with clean, generic prose that sounds helpful but has lost the specific facts, edge cases, and decision rationale that matter during real work.",
  },
];

const principles = [
  {
    title: "Evidence-Grounded Memory",
    anchor: "Tulving's episodic and semantic memory model",
    body:
      "Borg treats conversations as episodic memory and extracted facts as semantic memory. The offline pipeline turns raw episodes into structured facts, procedures, and entities with provenance. That gives the system something it can compare, supersede, and rank instead of treating an old conversation chunk as permanent truth.",
  },
  {
    title: "Prefer Fragmentation Over Collision",
    anchor: "Fellegi-Sunter record linkage theory",
    body:
      "When entity resolution is uncertain, Borg would rather keep two references separate than merge the wrong things together. A false merge poisons every downstream fact. A temporary split is inconvenient, but recoverable. That tradeoff is the right one when the output feeds an LLM that will reason over bad context with confidence.",
  },
  {
    title: "Faceted Retrieval Under Budget",
    anchor: "Faceted retrieval and constrained ranking",
    body:
      "Borg does not bet everything on one ranked list. It retrieves across entities, facts, procedures, and snapshots, then applies memory-type weights per task and namespace. That makes context selection more robust when the real budget is not documents, but a few thousand tokens inside a model window.",
  },
  {
    title: "Temporal Consistency Through Supersession",
    anchor: "Bitemporal data management",
    body:
      "Facts in Borg have a lifecycle. They are not merely true or false. They are observed, current, superseded, or archived with valid time and recording time. That prevents the classic memory failure where a system retrieves both \"Python 3.9\" and \"Python 3.12\" with no attempt to resolve which one still applies.",
  },
  {
    title: "Namespace Scoping and Token Budgets",
    anchor: "Lost in the Middle and resource-aware retrieval",
    body:
      "LLMs do worse when useful context is diluted by unrelated material. Borg scopes memory by namespace before retrieval and applies configurable token budgets per namespace. Context is treated like a scarce runtime resource, not an infinite dump target.",
  },
  {
    title: "PostgreSQL as the Source of Truth",
    anchor: "Consistency over system sprawl",
    body:
      "pgvector covers similarity search. Recursive CTEs cover graph traversal. ACID transactions keep mutations coherent. pgAudit preserves traceability. A separate vector database or graph store adds new consistency boundaries and new failure modes. Borg stays PostgreSQL-native to avoid an entire class of distributed-state bugs.",
  },
];

export default function SciencePage() {
  return (
    <div className="pt-16">
      <div className="border-b border-[var(--border)] bg-gradient-to-b from-[var(--accent-blue)]/5 to-transparent">
        <div className="mx-auto max-w-6xl px-6 pb-12 pt-20">
          <h1 className="text-4xl font-extrabold text-[var(--text-primary)]">
            The Science Behind Borg
          </h1>
          <p className="mt-4 max-w-3xl text-lg text-[var(--text-secondary)]">
            Borg&apos;s memory architecture is not an aesthetic choice. It is a response to how
            memory fails in LLM systems, and it is grounded in cognitive science,
            information retrieval, temporal data management, and database design.
          </p>
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-[var(--text-muted)]">
            The core claim is simple: LLM memory is not a search problem. It is a
            knowledge compilation problem.
          </p>
        </div>
      </div>

      <Section
        id="problem"
        title="The Core Problem"
        subtitle="LLMs are stateless inference engines. Every call starts from zero, so the memory layer has to do more than retrieve text."
      >
        <div className="grid gap-6 lg:grid-cols-2">
          {flawedApproaches.map((approach) => (
            <div
              key={approach.title}
              className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6"
            >
              <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-red)]">
                Common Approach
              </p>
              <h2 className="mt-3 text-2xl font-bold text-[var(--text-primary)]">
                {approach.title}
              </h2>
              <p className="mt-3 text-sm text-[var(--text-secondary)]">{approach.summary}</p>
              <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
                {approach.whyItFails}
              </p>
            </div>
          ))}
        </div>
      </Section>

      <Section
        id="principles"
        title="Why Borg Takes a Different Path"
        subtitle="Each major design choice solves a real failure mode in LLM memory systems."
        className="border-t border-[var(--border)]"
      >
        <div className="grid gap-6 lg:grid-cols-2">
          {principles.map((principle) => (
            <div
              key={principle.title}
              className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6"
            >
              <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-blue)]">
                Scientific Anchor
              </p>
              <p className="mt-2 text-sm font-medium text-[var(--text-muted)]">
                {principle.anchor}
              </p>
              <h3 className="mt-4 text-xl font-semibold text-[var(--text-primary)]">
                {principle.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)]">
                {principle.body}
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* Measured Results */}
      <Section
        id="measured"
        title="Measured Results (April 2026)"
        subtitle="The compilation thesis tested on real production episodes from cloud-infrastructure engineering."
        className="border-t border-[var(--border)]"
      >
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
          <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
            Across 10 benchmark tasks, Borg compiled context (C) achieved 10/10 task
            success compared to 8/10 for vector RAG (B) and 0/10 for no memory (A).
            Retrieval precision reached 0.913, with a 78% lower stale fact rate and
            61% less irrelevant content than vector RAG. Knowledge coverage improved
            by 16% (0.908 vs 0.782).
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
            The gain comes from what is included, not from using fewer tokens — context
            token counts are comparable between B and C (2,806 vs 3,026). Full benchmark
            methodology and per-task results are on the{" "}
            <Link href="/benchmarks" className="text-[var(--accent-green)] hover:underline">
              benchmarks page
            </Link>.
          </p>
        </div>
      </Section>

      <Section
        id="compilation"
        title="Compilation, Not Search"
        subtitle="This is the architectural bet underneath the whole system."
        className="border-t border-[var(--border)]"
      >
        <div className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              RAG treats memory as a search problem: query in, documents out. Borg treats
              memory as a compilation problem: messy source material goes through a sequence
              of extraction, validation, resolution, supersession, ranking, and formatting
              passes before any context reaches a model.
            </p>
            <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
              The compiler analogy is literal. Source code is redundant, inconsistent, and
              written for humans. A compiler turns it into a smaller, structured artifact that
              machines can use. Conversations are the same. They are contradictory, local,
              emotional, and full of dead ends. Borg&apos;s offline pipeline compiles them into
              memory that can be trusted enough to retrieve.
            </p>
            <p className="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
              That is why the pipeline has multiple passes. Embeddings, entity extraction,
              three-pass resolution, fact extraction, supersession, serving-state updates,
              procedure extraction, and snapshots each preserve a guarantee you lose if you
              cut the step out.
            </p>
          </div>

          <div className="rounded-xl border border-[var(--accent-green)]/30 bg-[var(--accent-green)]/5 p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--accent-green)]">
              Bottom Line
            </p>
            <p className="mt-4 text-lg font-semibold leading-relaxed text-[var(--text-primary)]">
              The systems that win at AI memory will treat it as data engineering, not vector
              search with better marketing.
            </p>
            <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
              Borg is built around that assumption from the start.
            </p>
          </div>
        </div>
      </Section>

      <Section
        id="next"
        title="See The Implementation"
        subtitle="The theory only matters if the runtime and data model reflect it."
        className="border-t border-[var(--border)]"
      >
        <div className="flex flex-wrap gap-4">
          <Link
            href="/architecture"
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent-green)] px-6 py-3 text-sm font-semibold text-[var(--bg-primary)] transition-all hover:brightness-110"
          >
            Open Architecture
          </Link>
          <Link
            href="/features"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--border-accent)] px-6 py-3 text-sm font-semibold text-[var(--text-primary)] transition-all hover:border-[var(--accent-green)]/50 hover:bg-[var(--bg-card)]"
          >
            Review Features
          </Link>
        </div>
      </Section>
    </div>
  );
}
