"""Stage 5: Compile selected candidates into model-specific output."""


async def compile_package(
    selected: list[dict],
    namespace: str,
    task_class: str,
    model: str,
    fmt: str,
) -> tuple[str, int]:
    """Compile selected candidates into a context package.

    Returns (compiled_text, token_count).
    """
    if fmt == "structured":
        return _compile_structured(selected, namespace, task_class, model)
    else:
        return _compile_compact(selected, namespace, task_class)


def _compile_structured(
    selected: list[dict], namespace: str, task_class: str, model: str
) -> tuple[str, int]:
    """XML-structured format for Claude / Copilot."""
    facts = [c for c in selected if c["type"] in ("fact", "graph_fact")]
    episodes = [c for c in selected if c["type"] == "episode"]
    procedures = [c for c in selected if c["type"] == "procedure"]

    lines = [f'<borg model="{model}" ns="{namespace}" task="{task_class}">']

    if facts:
        lines.append("  <knowledge>")
        for f in facts:
            status = f.get("evidence_status", "extracted")
            score = f.get("scores", {}).get("composite", 0)
            lines.append(
                f'    <fact status="{status}" salience="{score:.2f}">{f["content"]}</fact>'
            )
        lines.append("  </knowledge>")

    if episodes:
        lines.append("  <episodes>")
        for e in episodes:
            src = e.get("source", "unknown")
            dt = e.get("occurred_at", "")[:10] if e.get("occurred_at") else ""
            content = e["content"]
            lines.append(f'    <episode source="{src}" date="{dt}">{content}</episode>')
        lines.append("  </episodes>")

    if procedures:
        lines.append("  <patterns>")
        for p in procedures:
            conf = p.get("confidence", 0)
            lines.append(f'    <procedure confidence="{conf:.2f}">{p["content"]}</procedure>')
        lines.append("  </patterns>")

    lines.append("</borg>")

    compiled = "\n".join(lines)
    tokens = len(compiled) // 4  # rough estimate
    return compiled, tokens


def _compile_compact(selected: list[dict], namespace: str, task_class: str) -> tuple[str, int]:
    """JSON-compact format for GPT / Codex / local models."""
    import json

    facts = [c["content"] for c in selected if c["type"] in ("fact", "graph_fact")]
    episodes = [
        f"{c.get('occurred_at', '')[:10]}: {c['content']}"
        for c in selected
        if c["type"] == "episode"
    ]
    procedures = [c["content"] for c in selected if c["type"] == "procedure"]

    obj = {"ns": namespace, "task": task_class}
    if facts:
        obj["facts"] = facts
    if episodes:
        obj["recent"] = episodes
    if procedures:
        obj["patterns"] = procedures

    compiled = json.dumps(obj, ensure_ascii=False)
    tokens = len(compiled) // 4
    return compiled, tokens
