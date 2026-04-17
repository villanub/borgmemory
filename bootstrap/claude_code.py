"""Transform Claude Code JSONL sessions into Borg episodes.

Claude Code stores sessions in ~/.claude/projects/<encoded-path>/sessions/*.jsonl
Each line is a JSON object with: sessionId, cwd, type (user/assistant/tool_use/tool_result),
message (with role + content), timestamp, parentUuid, uuid.

The session filename is the session UUID.
"""

import json
from pathlib import Path


def transform_claude_code_sessions(base_path: str, namespace: str, min_messages: int = 4) -> list[dict]:
    """Read all Claude Code JSONL sessions and transform to Borg episodes.

    Args:
        base_path: Path to ~/.claude/projects (or override)
        namespace: Borg namespace to assign
        min_messages: Minimum user+assistant messages to include a session
    """
    base = Path(base_path).expanduser()
    episodes = []

    # Claude Code stores sessions as:
    # ~/.claude/projects/<encoded-path>/sessions/<session-uuid>.jsonl
    # or directly as ~/.claude/projects/<encoded-path>/<session-uuid>.jsonl
    for jsonl_file in sorted(base.rglob("*.jsonl")):
        try:
            episode = _parse_session(jsonl_file, namespace, min_messages)
            if episode:
                episodes.append(episode)
        except Exception as e:
            print(f"  Warning: Failed to parse {jsonl_file.name}: {e}")

    return episodes


def _parse_session(jsonl_file: Path, namespace: str, min_messages: int) -> dict | None:
    """Parse a single Claude Code JSONL session file."""
    entries = []
    with open(jsonl_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not entries:
        return None

    # Extract metadata from first entry
    session_id = entries[0].get("sessionId", jsonl_file.stem)
    project_dir = entries[0].get("cwd", "")
    first_ts = entries[0].get("timestamp")

    # Build conversation text
    text_parts = []
    files_touched = set()

    for entry in entries:
        msg = entry.get("message", {})
        role = msg.get("role", "")

        if role == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                )
            if content.strip():
                text_parts.append(f"User: {content.strip()[:2000]}")

        elif role == "assistant":
            content_parts = msg.get("content", [])
            if isinstance(content_parts, str):
                text = content_parts
            elif isinstance(content_parts, list):
                texts = []
                for part in content_parts:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            texts.append(part.get("text", ""))
                        elif part.get("type") == "tool_use":
                            tool = part.get("name", "unknown")
                            inp = part.get("input", {})
                            file = inp.get("file_path", inp.get("path", inp.get("command", "")))
                            if file:
                                files_touched.add(str(file)[:200])
                            texts.append(f"[Tool: {tool} → {file}]")
                text = "\n".join(texts)
            else:
                text = ""
            if text.strip():
                text_parts.append(f"Claude: {text.strip()[:2000]}")

    # Count actual conversation messages (not tool calls)
    message_count = sum(1 for p in text_parts if p.startswith(("User:", "Claude:")))
    if message_count < min_messages:
        return None

    content = "\n\n".join(text_parts)
    if len(content) < 200:
        return None

    return {
        "source": "claude-code",
        "source_id": session_id,
        "source_event_id": f"claude-code-{session_id}",
        "content": content,
        "occurred_at": first_ts or None,
        "namespace": namespace,
        "metadata": {
            "project_dir": project_dir,
            "session_id": session_id,
            "files_touched": sorted(files_touched)[:20],
            "message_count": message_count,
        },
        "participants": ["user", "claude-code"],
    }
