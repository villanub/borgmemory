"""Transform a manual markdown knowledge dump into Borg episodes."""

import hashlib
from datetime import datetime


def transform_manual_knowledge(filepath: str, namespace: str, title: str = "Manual knowledge dump") -> list[dict]:
    with open(filepath) as f:
        content = f.read()

    return [{
        "source": "manual",
        "source_id": f"manual-{hashlib.md5(filepath.encode()).hexdigest()[:8]}",
        "source_event_id": f"manual-{filepath}",
        "content": content,
        "occurred_at": datetime.now().isoformat(),
        "namespace": namespace,
        "metadata": {"title": title, "type": "knowledge_dump"},
        "participants": ["user"],
    }]
