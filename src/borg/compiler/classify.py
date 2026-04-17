"""Stage 1: Intent classification — dual-profile with fallback.

Amendment 3: Returns primary + secondary class with confidences.
Both profiles run retrieval. Candidates merge before ranking.
This eliminates the single-path classification failure mode.
"""

from dataclasses import dataclass

TASK_KEYWORDS = {
    "debug": [
        "bug",
        "error",
        "fix",
        "broken",
        "fail",
        "retry",
        "exception",
        "crash",
        "debug",
        "issue",
        "troubleshoot",
    ],
    "architecture": [
        "design",
        "architect",
        "pattern",
        "structure",
        "diagram",
        "component",
        "service",
        "system",
        "integration",
        "how does",
    ],
    "compliance": [
        "sox",
        "audit",
        "compliance",
        "policy",
        "decision",
        "history",
        "when did",
        "who approved",
        "what changed",
        "what happened",
    ],
    "writing": [
        "write",
        "draft",
        "proposal",
        "rfp",
        "email",
        "document",
        "report",
        "summarize",
        "value proposition",
    ],
}

PROFILE_MAP = {
    "debug": ["graph_neighborhood", "episode_recall"],
    "architecture": ["fact_lookup", "graph_neighborhood", "episode_recall"],
    "compliance": ["episode_recall", "fact_lookup"],
    "writing": ["fact_lookup"],
    "chat": ["fact_lookup"],
}

# Memory type weight modifiers per task class.
# (episodic, semantic, procedural) — biases ranking, not hard-excludes.
# 0.0 = hard exclude (procedural in compliance only).
MEMORY_WEIGHT_MODIFIERS = {
    "debug": (1.0, 0.7, 0.8),
    "architecture": (0.5, 1.0, 0.3),
    "compliance": (1.0, 0.8, 0.0),
    "writing": (0.3, 1.0, 0.6),
    "chat": (0.4, 1.0, 0.3),
}


@dataclass
class ClassificationResult:
    primary_class: str
    secondary_class: str | None
    primary_confidence: float
    secondary_confidence: float | None
    retrieval_profiles: list[str]
    memory_weights: tuple[float, float, float]


async def classify_intent(query: str, task_hint: str | None = None) -> ClassificationResult:
    """Classify query into primary + secondary task class.

    Returns merged retrieval profiles from both classes.
    """
    if task_hint and task_hint in PROFILE_MAP:
        return ClassificationResult(
            primary_class=task_hint,
            secondary_class=None,
            primary_confidence=1.0,
            secondary_confidence=None,
            retrieval_profiles=PROFILE_MAP[task_hint],
            memory_weights=MEMORY_WEIGHT_MODIFIERS[task_hint],
        )

    query_lower = query.lower()
    scores: dict[str, int] = {}

    for task, keywords in TASK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[task] = score

    if not scores:
        return ClassificationResult(
            primary_class="chat",
            secondary_class=None,
            primary_confidence=0.5,
            secondary_confidence=None,
            retrieval_profiles=PROFILE_MAP["chat"],
            memory_weights=MEMORY_WEIGHT_MODIFIERS["chat"],
        )

    sorted_tasks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    total = sum(s for _, s in sorted_tasks)

    primary = sorted_tasks[0]
    primary_conf = primary[1] / total if total > 0 else 0.5

    secondary = None
    secondary_conf = None

    if len(sorted_tasks) > 1:
        sec = sorted_tasks[1]
        sec_conf = sec[1] / total if total > 0 else 0
        # Include secondary if confidence gap < 0.3
        if primary_conf - sec_conf < 0.3:
            secondary = sec[0]
            secondary_conf = sec_conf

    # Merge retrieval profiles: primary + secondary (deduplicated, capped at 3)
    profiles = list(PROFILE_MAP[primary[0]])
    if secondary:
        for p in PROFILE_MAP[secondary]:
            if p not in profiles:
                profiles.append(p)
    profiles = profiles[:3]

    return ClassificationResult(
        primary_class=primary[0],
        secondary_class=secondary,
        primary_confidence=round(primary_conf, 3),
        secondary_confidence=round(secondary_conf, 3) if secondary_conf else None,
        retrieval_profiles=profiles,
        memory_weights=MEMORY_WEIGHT_MODIFIERS[primary[0]],
    )
