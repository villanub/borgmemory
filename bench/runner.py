"""Borg benchmark runner — orchestrates A/B/C conditions across all tasks.

Usage:
    python -m bench.runner                    # Run all tasks, all conditions
    python -m bench.runner --task task-01     # Run one task
    python -m bench.runner --condition C      # Run one condition across all tasks
    python -m bench.runner --report           # Generate report from existing results
    python -m bench.runner --dry-run          # Print plan without executing
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from bench.conditions import borg_compiled, no_memory, simple_retrieval
from bench.config import cfg
from bench.evaluator import evaluate
from bench.report import generate_report

TASKS_FILE = Path("bench/tasks.json")
RESULTS_DIR = Path("bench/results")


def _setup_logging(results_dir: Path, timestamp: str):
    """Configure logging to console (INFO) and file (DEBUG)."""
    results_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / f"bench_{timestamp}.log"

    root = logging.getLogger("bench")
    root.setLevel(logging.DEBUG)

    # Console: INFO
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", datefmt="%H:%M:%S")
    )
    root.addHandler(ch)

    # File: DEBUG (captures full request/response detail)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))
    root.addHandler(fh)

    root.info(f"Logging to {log_file}")
    return log_file


def load_tasks(task_filter: str | None = None) -> list[dict]:
    with open(TASKS_FILE) as f:
        data = json.load(f)
    tasks = data["tasks"]
    if task_filter:
        tasks = [t for t in tasks if t["id"] == task_filter]
        if not tasks:
            print(f"Error: task '{task_filter}' not found in {TASKS_FILE}")
            sys.exit(1)
    return tasks


CONDITION_MAP = {
    "A": no_memory,
    "B": simple_retrieval,
    "C": borg_compiled,
}


async def run_single(task: dict, condition: str) -> dict:
    """Run a single task under a single condition."""
    module = CONDITION_MAP[condition]
    print(f"  [{condition}] Running {task['id']}...", end=" ", flush=True)
    try:
        result = await module.run(task)
        print(f"done ({result.get('latency_ms', '?')}ms)")
        return result
    except Exception as e:
        print(f"FAILED: {e}")
        return {
            "condition": condition,
            "task_id": task["id"],
            "response": "",
            "context_injected": None,
            "context_tokens": 0,
            "latency_ms": 0,
            "error": str(e),
        }


async def evaluate_result(task: dict, result: dict) -> dict:
    """Evaluate a single result using LLM-as-judge."""
    cond = result["condition"]
    tid = result["task_id"]
    print(f"  [JUDGE] Evaluating {tid}/{cond}...", end=" ", flush=True)
    try:
        scores = await evaluate(task, result)
        print("done")
        return scores
    except Exception as e:
        print(f"FAILED: {e}")
        return {
            "condition": cond,
            "task_id": tid,
            "error": str(e),
        }


def save_result(result: dict, prefix: str = "run"):
    """Save a result to the results directory."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    tid = result.get("task_id", "unknown")
    cond = result.get("condition", "X")
    path = RESULTS_DIR / f"{prefix}_{tid}_{cond}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    return path


async def main():
    parser = argparse.ArgumentParser(description="Borg benchmark runner")
    parser.add_argument("--task", help="Run only this task ID")
    parser.add_argument("--condition", choices=["A", "B", "C"], help="Run only this condition")
    parser.add_argument(
        "--report", action="store_true", help="Generate report from existing results"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without executing")
    parser.add_argument("--skip-eval", action="store_true", help="Skip LLM-as-judge evaluation")
    parser.add_argument(
        "--run-timestamp",
        help="Timestamp of a prior run to regenerate report for (e.g. 20260415_143022)",
    )
    args = parser.parse_args()

    if args.report:
        report = generate_report(run_timestamp=args.run_timestamp)
        print(report)
        out = RESULTS_DIR / "report.md"
        out.write_text(report)
        print(f"\nReport written to {out}")
        return

    tasks = load_tasks(args.task)
    conditions = [args.condition] if args.condition else ["A", "B", "C"]

    # Print plan
    print("\nBorg Benchmark Runner")
    print(f"{'=' * 50}")
    print(f"Tasks:      {len(tasks)}")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Total runs: {len(tasks) * len(conditions)}")
    print(f"Namespace:  {cfg.namespace}")
    print(f"Borg URL:   {cfg.borg_url}")
    print(f"Task model: {cfg.task_model}")
    print(f"Judge model:{cfg.judge_model}")
    print(f"Results:    {RESULTS_DIR}")
    print()

    if args.dry_run:
        print("Dry run — would execute:")
        for task in tasks:
            for cond in conditions:
                print(f"  {task['id']} / condition {cond} ({task['task_class']})")
        return

    # Setup logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _setup_logging(RESULTS_DIR, timestamp)

    # Preflight check
    if "C" in conditions:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{cfg.borg_url}/health")
                r.raise_for_status()
                print("Borg engine: healthy")
        except Exception as e:
            print(f"ERROR: Cannot reach Borg engine at {cfg.borg_url}: {e}")
            print("Condition C requires a running Borg engine. Start it with: docker compose up -d")
            sys.exit(1)

    # Run
    all_results = []

    for task in tasks:
        print(f"\n{'─' * 40}")
        print(f"Task: {task['id']} — {task['description']}")
        print(f'Query: "{task["query"]}"')
        print(f"Class: {task['task_class']}")

        task_results = {}
        for cond in conditions:
            result = await run_single(task, cond)
            save_result(result, prefix=f"run_{timestamp}")
            task_results[cond] = result
            all_results.append(result)

        # Evaluate
        if not args.skip_eval:
            for cond in conditions:
                result = task_results[cond]
                if result.get("error"):
                    continue
                scores = await evaluate_result(task, result)
                save_result(scores, prefix=f"eval_{timestamp}")

    # Generate report scoped to this run
    print(f"\n{'=' * 50}")
    print("Generating report...")
    report = generate_report(run_timestamp=timestamp)
    out = RESULTS_DIR / f"report_{timestamp}.md"
    out.write_text(report)
    print(f"Report written to {out}")

    # Also write latest
    latest = RESULTS_DIR / "report.md"
    latest.write_text(report)
    print(f"Latest report: {latest}")


if __name__ == "__main__":
    asyncio.run(main())
