"""Transform Claude.ai export JSON into Borg episodes."""

import json
from datetime import datetime


def transform_claude_export(filepath: str, namespace: str) -> list[dict]:
    with open(filepath) as f:
        conversations = json.load(f)

    episodes = []
    for conv in conversations:
        messages = conv.get("chat_messages", [])
        if not messages:
            continue

        text_parts = []
        for msg in messages:
            role = "Human" if msg.get("sender") == "human" else "Claude"
            text_parts.append(f"{role}: {msg.get('text', '')}")

        content = "\n\n".join(text_parts)
        if len(content) < 200:
            continue

        episode = {
            "source": "claude.ai",
            "source_id": conv.get("uuid", ""),
            "source_event_id": f"claude-ai-{conv.get('uuid', '')}",
            "content": content,
            "occurred_at": conv.get("created_at", datetime.now().isoformat()),
            "namespace": namespace,
            "metadata": {
                "title": conv.get("name", "Untitled"),
                "message_count": len(messages),
            },
            "participants": ["user", "claude"],
        }
        episodes.append(episode)

    return episodes
