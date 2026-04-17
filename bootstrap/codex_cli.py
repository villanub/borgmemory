"""Transform Codex CLI rollout JSONL files into Borg episodes.

Codex CLI stores sessions as rollout-*.jsonl files under:
  ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl

Each line is a JSON object. The format varies by event type:
- Metadata header: session_id, source, timestamp, model_provider
- User turns: type "user", content as text
- Assistant turns: type "assistant", content as text or structured
- Tool calls: type "function_call" with name + arguments
"""

import json
from datetime import datetime
from pathlib import Path


def transform_codex_sessions(
    base_path: str,
    namespace: str,
    min_interactions: int = 4,
) -> list[dict]:
    """Read all Codex CLI rollout files and transform to Borg episodes.

    Args:
        base_path: Path to ~/.codex/sessions (or ~/.codex for broader search)
        namespace: Borg namespace to assign
        min_interactions: Minimum user+assistant messages to include
    """
    base = Path(base_path).expanduser()
    episodes = []

    # Codex stores rollouts as:
    # ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
    for jsonl_file in sorted(base.rglob("rollout-*.jsonl")):
        try:
            episode = _parse_rollout(jsonl_file, namespace, min_interactions)
            if episode:
                episodes.append(episode)
        except Exception as e:
            print(f"  Warning: Failed to parse {jsonl_file.name}: {e}")

    return episodes


def _parse_rollout(jsonl_file: Path, namespace: str, min_interactions: int) -> dict | None:
    """Parse a single Codex CLI rollout JSONL file."""
    events = []
    with open(jsonl_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not events:
        return None

    text_parts = []
    first_ts = None
    session_id = None
    model_used = "unknown"
    cwd = None
    files_touched = set()

    for event in events:
        ts = event.get("timestamp", "")
        if not first_ts and ts:
            first_ts = ts

        # Extract metadata from header
        if not session_id:
            session_id = event.get("session_id", event.get("sessionId", ""))
        if not cwd:
            cwd = event.get("cwd", "")
        if event.get("model"):
            model_used = event["model"]

        # Handle different event formats
        evt_type = event.get("type", "")
        role = event.get("role", "")

        # Format 1: type-based (older Codex)
        if evt_type == "message" or role in ("user", "assistant"):
            actual_role = role or evt_type
            content = event.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                )
            if not content.strip():
                continue
            label = "User" if actual_role == "user" else "Codex"
            text_parts.append(f"{label}: {content.strip()[:2000]}")

        # Format 2: payload-based (newer Codex)
        elif "payload" in event:
            payload = event["payload"]
            p_type = payload.get("type", "")
            if p_type == "message":
                p_role = payload.get("role", "unknown")
                p_content = payload.get("content", "")
                if isinstance(p_content, list):
                    p_content = " ".join(
                        p.get("text", "") if isinstance(p, dict) else str(p)
                        for p in p_content
                    )
                if not p_content.strip():
                    continue
                label = "User" if p_role == "user" else "Codex"
                text_parts.append(f"{label}: {p_content.strip()[:2000]}")
            elif p_type in ("tool_use", "function_call"):
                tool = payload.get("tool", payload.get("name", "unknown"))
                file = payload.get("file", payload.get("path", ""))
                cmd = payload.get("command", payload.get("arguments", ""))
                if file:
                    files_touched.add(str(file)[:200])
                detail = file or (str(cmd)[:100] if cmd else "")
                text_parts.append(f"[Tool: {tool} → {detail}]")
            elif p_type == "token_count":
                model_used = payload.get("model", model_used)

        # Format 3: function_call at top level
        elif evt_type == "function_call":
            name = event.get("name", "unknown")
            args = event.get("arguments", "")
            text_parts.append(f"[Tool: {name} → {str(args)[:100]}]")

    # Count actual conversation messages
    message_count = sum(1 for p in text_parts if p.startswith(("User:", "Codex:")))
    if message_count < min_interactions:
        return None

    content = "\n\n".join(text_parts)
    if len(content) < 200:
        return None

    # Use filename as session ID if not found in data
    if not session_id:
        session_id = jsonl_file.stem.replace("rollout-", "")

    return {
        "source": "codex-cli",
        "source_id": session_id,
        "source_event_id": f"codex-{session_id}",
        "content": content,
        "occurred_at": first_ts or datetime.now().isoformat(),
        "namespace": namespace,
        "metadata": {
            "session_id": session_id,
            "model": model_used,
            "message_count": message_count,
            "cwd": cwd or "",
            "files_touched": sorted(files_touched)[:20],
        },
        "participants": ["user", "codex"],
    }
