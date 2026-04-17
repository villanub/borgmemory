# CLAUDE.md — Project Borg

## Borg Namespace

For this repository, use Borg namespace `borg`.

Always pass `namespace="borg"` to:
- `borg_think`
- `borg_learn`
- `borg_recall`

Do not omit the namespace.
Do not use `default` for work in this repository.

## When to use Borg

### borg_think

Call `borg_think` before complex tasks to retrieve relevant project context, prior decisions, and working patterns.

Use:
- When starting work on a file or module you have not touched in the current session
- When debugging
- When making architecture or design decisions
- When writing docs, proposals, or project explanations

Example:

```python
borg_think(
    query="Project Borg repository context, recent decisions, and active development areas",
    namespace="borg",
    task_hint="architecture",
)
```

### borg_learn

Call `borg_learn` after significant decisions, discoveries, or non-obvious fixes that should persist across sessions.

Example:

```python
borg_learn(
    content="Fixed auth issue in Borg. Root cause was ... Solution was ...",
    source="claude-code",
    namespace="borg",
)
```

### borg_recall

Call `borg_recall` for direct searches when you want raw memory rather than compiled context.

Example:

```python
borg_recall(
    query="Entra auth migration",
    namespace="borg",
    memory_type="semantic",
)
```
