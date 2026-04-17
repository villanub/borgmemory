"""Report generator — produces decision gate analysis from benchmark results.

Reads all evaluated results and generates:
1. Per-task comparison table (A vs B vs C)
2. Aggregate metrics per condition
3. Decision gate verdict (proceed / simplify / stop)
"""

import json
import statistics
from datetime import datetime
from pathlib import Path


def generate_report(results_dir: str = "bench/results", run_timestamp: str | None = None) -> str:
    """Load evaluated results and produce a markdown report.

    Args:
        results_dir: Directory containing eval_*.json files.
        run_timestamp: If provided (e.g. "20260415_143022"), scope report to that
            run only. If None, defaults to the most recent run's timestamp.
    """
    p = Path(results_dir)
    if not p.exists():
        return "# Benchmark Report\n\nNo results found."

    all_eval_files = sorted(p.glob("eval_*.json"))
    if not all_eval_files:
        return "# Benchmark Report\n\nNo evaluated results found."

    if run_timestamp is None:
        # Derive timestamps from filenames: eval_YYYYMMDD_HHMMSS_task-xx_Y.json
        timestamps = sorted(
            {f.name.split("_")[1] + "_" + f.name.split("_")[2] for f in all_eval_files}
        )
        run_timestamp = timestamps[-1]  # latest

    eval_files = sorted(p.glob(f"eval_{run_timestamp}_*.json"))
    if not eval_files:
        return f"# Benchmark Report\n\nNo results found for run {run_timestamp}."

    all_evals = []
    for f in eval_files:
        with open(f) as fh:
            all_evals.append(json.load(fh))

    # Group by task and condition
    by_task: dict[str, dict[str, dict]] = {}
    for ev in all_evals:
        tid = ev["task_id"]
        cond = ev["condition"]
        by_task.setdefault(tid, {})[cond] = ev

    # Aggregate by condition
    by_condition: dict[str, list[dict]] = {"A": [], "B": [], "C": []}
    for ev in all_evals:
        by_condition[ev["condition"]].append(ev)

    lines = []
    lines.append("# Borg Benchmark Report")
    lines.append(f"\nGenerated: {datetime.now().isoformat()[:19]}")
    lines.append(f"Run: {run_timestamp}")
    lines.append(f"\nTasks evaluated: {len(by_task)}")
    lines.append(f"Total runs: {len(all_evals)}")

    # ── Per-task comparison ──
    lines.append("\n---\n\n## Per-Task Results\n")
    lines.append(
        "| Task | Cond | Success | Precision | Stale | Irrelevant | Coverage | Tokens | Latency |"
    )
    lines.append(
        "|------|------|---------|-----------|-------|------------|----------|--------|---------|"
    )

    for tid in sorted(by_task.keys()):
        for cond in ["A", "B", "C"]:
            ev = by_task[tid].get(cond)
            if not ev:
                continue
            lines.append(
                f"| {tid} | {cond} "
                f"| {ev.get('task_success', '?')} "
                f"| {_fmt(ev.get('retrieval_precision'))} "
                f"| {_fmt(ev.get('stale_fact_rate'))} "
                f"| {_fmt(ev.get('irrelevant_rate'))} "
                f"| {_fmt(ev.get('knowledge_coverage'))} "
                f"| {ev.get('context_tokens', 0)} "
                f"| {ev.get('latency_ms', 0)}ms |"
            )

    # ── Aggregate metrics ──
    lines.append("\n---\n\n## Aggregate Metrics\n")
    lines.append("| Metric | A (No Memory) | B (Simple RAG) | C (Borg Compiled) | C vs B Delta |")
    lines.append("|--------|---------------|----------------|--------------------|--------------| ")

    for metric, label, higher_better in [
        ("task_success", "Task Success Rate", True),
        ("retrieval_precision", "Retrieval Precision", True),
        ("stale_fact_rate", "Stale Fact Rate", False),
        ("irrelevant_rate", "Irrelevant Rate", False),
        ("knowledge_coverage", "Knowledge Coverage", True),
        ("context_tokens", "Avg Context Tokens", False),
        ("latency_ms", "Avg Latency (ms)", False),
    ]:
        a_vals = [e.get(metric) for e in by_condition["A"] if e.get(metric) is not None]
        b_vals = [e.get(metric) for e in by_condition["B"] if e.get(metric) is not None]
        c_vals = [e.get(metric) for e in by_condition["C"] if e.get(metric) is not None]

        a_avg = _mean(a_vals)
        b_avg = _mean(b_vals)
        c_avg = _mean(c_vals)

        if b_avg is not None and c_avg is not None and b_avg != 0:
            delta_pct = ((c_avg - b_avg) / abs(b_avg)) * 100
            delta_str = f"{delta_pct:+.1f}%"
        else:
            delta_str = "N/A"

        lines.append(f"| {label} | {_fmt(a_avg)} | {_fmt(b_avg)} | {_fmt(c_avg)} | {delta_str} |")

    # ── Decision gate ──
    lines.append("\n---\n\n## Decision Gate\n")

    b_precision = _mean(
        [
            e.get("retrieval_precision")
            for e in by_condition["B"]
            if e.get("retrieval_precision") is not None
        ]
    )
    c_precision = _mean(
        [
            e.get("retrieval_precision")
            for e in by_condition["C"]
            if e.get("retrieval_precision") is not None
        ]
    )
    b_tokens = _mean(
        [e.get("context_tokens") for e in by_condition["B"] if e.get("context_tokens") is not None]
    )
    c_tokens = _mean(
        [e.get("context_tokens") for e in by_condition["C"] if e.get("context_tokens") is not None]
    )
    b_success = _mean(
        [e.get("task_success") for e in by_condition["B"] if e.get("task_success") is not None]
    )
    c_success = _mean(
        [e.get("task_success") for e in by_condition["C"] if e.get("task_success") is not None]
    )

    # Precision improvement
    if b_precision and c_precision and b_precision > 0:
        prec_delta = ((c_precision - b_precision) / b_precision) * 100
        prec_pass = prec_delta >= 15.0
    else:
        prec_delta = None
        prec_pass = False

    # Token reduction
    if b_tokens and c_tokens and b_tokens > 0:
        token_delta = ((c_tokens - b_tokens) / b_tokens) * 100
        token_pass = token_delta <= -30.0
    else:
        token_delta = None
        token_pass = False

    # Task success non-regression
    if b_success is not None and c_success is not None:
        success_pass = c_success >= b_success
    else:
        success_pass = False

    lines.append("| Criterion | Threshold | Actual | Pass |")
    lines.append("|-----------|-----------|--------|------|")
    lines.append(
        f"| Precision improvement (C vs B) | ≥15% | {_fmt_pct(prec_delta)} | {'✅' if prec_pass else '❌'} |"
    )
    lines.append(
        f"| Token reduction (C vs B) | ≥30% reduction | {_fmt_pct(token_delta)} | {'✅' if token_pass else '❌'} |"
    )
    lines.append(
        f"| Task success non-regression | C ≥ B | {_fmt(c_success)} vs {_fmt(b_success)} | {'✅' if success_pass else '❌'} |"
    )

    all_pass = prec_pass and token_pass and success_pass
    some_pass = prec_pass or token_pass
    if all_pass:
        verdict = "**PROCEED** — Borg compiled (C) beats simple retrieval (B) on all criteria."
    elif not some_pass:
        verdict = "**STOP** — Borg compiled (C) does not outperform simple retrieval (B). Thesis disproven."
    else:
        verdict = (
            "**SIMPLIFY** — Mixed results. Investigate whether compilation overhead is justified."
        )

    lines.append(f"\n### Verdict: {verdict}")

    # ── Per-task reasoning ──
    lines.append("\n---\n\n## Evaluation Reasoning\n")
    for tid in sorted(by_task.keys()):
        lines.append(f"### {tid}\n")
        for cond in ["A", "B", "C"]:
            ev = by_task[tid].get(cond)
            if not ev:
                continue
            lines.append(f"**Condition {cond}:**")
            for key in [
                "task_success_reasoning",
                "retrieval_precision_reasoning",
                "stale_fact_reasoning",
                "irrelevant_reasoning",
                "knowledge_coverage_reasoning",
            ]:
                if key in ev:
                    label = key.replace("_reasoning", "").replace("_", " ").title()
                    lines.append(f"- {label}: {ev[key]}")
            lines.append("")

    return "\n".join(lines)


def _mean(vals: list) -> float | None:
    nums = [v for v in vals if v is not None and isinstance(v, (int, float))]
    return round(statistics.mean(nums), 3) if nums else None


def _fmt(val) -> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{val:.3f}"
    return str(val)


def _fmt_pct(val) -> str:
    if val is None:
        return "—"
    return f"{val:+.1f}%"


if __name__ == "__main__":
    report = generate_report()
    print(report)
    out = Path("bench/results/report.md")
    out.write_text(report)
    print(f"\nReport written to {out}")
