"""Transform ChatGPT conversations.json export into Borg episodes."""

import json
from datetime import datetime


def transform_chatgpt_export(filepath: str, namespace: str) -> list[dict]:
    with open(filepath) as f:
        conversations = json.load(f)

    episodes = []
    for conv in conversations:
        title = conv.get("title", "Untitled")
        create_time = conv.get("create_time", 0)
        mapping = conv.get("mapping", {})

        messages = []
        for node_id, node in mapping.items():
            msg = node.get("message")
            if not msg or not msg.get("content"):
                continue
            parts = msg["content"].get("parts", [])
            text = " ".join(str(p) for p in parts if isinstance(p, str))
            if not text.strip():
                continue
            role = msg.get("author", {}).get("role", "unknown")
            ts = msg.get("create_time", create_time)
            messages.append((ts, role, text))

        messages.sort(key=lambda x: x[0])
        if len(messages) < 2:
            continue

        text_parts = []
        for ts, role, text in messages:
            label = "Human" if role == "user" else "ChatGPT" if role == "assistant" else role
            text_parts.append(f"{label}: {text}")

        content = "\n\n".join(text_parts)
        if len(content) < 200:
            continue

        occurred = datetime.fromtimestamp(create_time).isoformat() if create_time else None

        episode = {
            "source": "chatgpt",
            "source_id": conv.get("id", ""),
            "source_event_id": f"chatgpt-{conv.get('id', '')}",
            "content": content,
            "occurred_at": occurred,
            "namespace": namespace,
            "metadata": {"title": title, "message_count": len(messages)},
            "participants": ["user", "chatgpt"],
        }
        episodes.append(episode)

    return episodes
