"""Bootstrap loader — orchestrates all sources and bulk-loads into Borg.

Usage:
    python -m bootstrap.loader azure-msp                  # All sources, azure-msp namespace
    python -m bootstrap.loader azure-msp --source claude-code  # Claude Code only
    python -m bootstrap.loader azure-msp --source codex        # Codex CLI only
    python -m bootstrap.loader azure-msp --source claude-ai    # Claude.ai export only
    python -m bootstrap.loader azure-msp --source chatgpt      # ChatGPT export only
    python -m bootstrap.loader azure-msp --source manual       # Manual knowledge dump only
"""

import asyncio
import sys

import httpx

BORG_URL = "http://localhost:8080/api"

# Default data locations
CLAUDE_CODE_SESSIONS = "~/.claude/projects"
CODEX_CLI_SESSIONS = "~/.codex/sessions"
CLAUDE_AI_EXPORT = "exports/claude_export/conversations.json"
CHATGPT_EXPORT = "exports/chatgpt_export/conversations.json"
MANUAL_KNOWLEDGE = "exports/knowledge_dump.md"


async def load_episodes(episodes: list[dict], batch_size: int = 10):
    """Bulk-load episodes into Borg via REST API."""
    async with httpx.AsyncClient(timeout=30) as client:
        loaded, skipped, errors = 0, 0, 0

        for i in range(0, len(episodes), batch_size):
            batch = episodes[i:i + batch_size]
            for ep in batch:
                try:
                    resp = await client.post(f"{BORG_URL}/learn", json=ep)
                    result = resp.json()
                    status = result.get("status", "")
                    if status == "duplicate":
                        skipped += 1
                    elif status in ("accepted", "queued"):
                        loaded += 1
                    else:
                        errors += 1
                        print(f"  Unexpected status: {result}")
                except Exception as e:
                    errors += 1
                    print(f"  Error: {e}")

            print(f"  Progress: {loaded} loaded, {skipped} skipped, {errors} errors")

        return {"loaded": loaded, "skipped": skipped, "errors": errors}


async def bootstrap(namespace: str = "default", source_filter: str | None = None):
    """Run the bootstrap pipeline.

    Args:
        namespace: Borg namespace to ingest into
        source_filter: If set, only load from this source (claude-code, codex, claude-ai, chatgpt, manual)
    """
    all_episodes = []
    sources = [source_filter] if source_filter else ["claude-code", "codex", "claude-ai", "chatgpt", "manual"]

    # Priority 1: Claude Code sessions
    if "claude-code" in sources:
        from bootstrap.claude_code import transform_claude_code_sessions
        try:
            print(f"[1/5] Loading Claude Code sessions from {CLAUDE_CODE_SESSIONS}...")
            eps = transform_claude_code_sessions(CLAUDE_CODE_SESSIONS, namespace)
            print(f"  Found {len(eps)} sessions")
            all_episodes += eps
        except Exception as e:
            print(f"  Skipped — {e}")

    # Priority 2: Codex CLI sessions
    if "codex" in sources:
        from bootstrap.codex_cli import transform_codex_sessions
        try:
            print(f"[2/5] Loading Codex CLI sessions from {CODEX_CLI_SESSIONS}...")
            eps = transform_codex_sessions(CODEX_CLI_SESSIONS, namespace)
            print(f"  Found {len(eps)} sessions")
            all_episodes += eps
        except Exception as e:
            print(f"  Skipped — {e}")

    # Priority 3: Claude.ai export
    if "claude-ai" in sources:
        from bootstrap.claude_ai import transform_claude_export
        try:
            print(f"[3/5] Loading Claude.ai conversations from {CLAUDE_AI_EXPORT}...")
            eps = transform_claude_export(CLAUDE_AI_EXPORT, namespace)
            print(f"  Found {len(eps)} conversations")
            all_episodes += eps
        except FileNotFoundError:
            print(f"  Skipped — file not found at {CLAUDE_AI_EXPORT}")

    # Priority 4: ChatGPT export
    if "chatgpt" in sources:
        from bootstrap.chatgpt import transform_chatgpt_export
        try:
            print(f"[4/5] Loading ChatGPT conversations from {CHATGPT_EXPORT}...")
            eps = transform_chatgpt_export(CHATGPT_EXPORT, namespace)
            print(f"  Found {len(eps)} conversations")
            all_episodes += eps
        except FileNotFoundError:
            print(f"  Skipped — file not found at {CHATGPT_EXPORT}")

    # Priority 5: Manual knowledge dump
    if "manual" in sources:
        from bootstrap.manual import transform_manual_knowledge
        try:
            print(f"[5/5] Loading manual knowledge from {MANUAL_KNOWLEDGE}...")
            eps = transform_manual_knowledge(MANUAL_KNOWLEDGE, namespace)
            print(f"  Found {len(eps)} entries")
            all_episodes += eps
        except FileNotFoundError:
            print(f"  Skipped — file not found at {MANUAL_KNOWLEDGE}")

    print(f"\nTotal episodes prepared: {len(all_episodes)}")

    if not all_episodes:
        print("\nNo episodes to load. Check data locations:")
        print(f"  Claude Code: {CLAUDE_CODE_SESSIONS}")
        print(f"  Codex CLI:   {CODEX_CLI_SESSIONS}")
        print(f"  Claude.ai:   {CLAUDE_AI_EXPORT}")
        print(f"  ChatGPT:     {CHATGPT_EXPORT}")
        print(f"  Manual:      {MANUAL_KNOWLEDGE}")
        return

    print(f"Loading into Borg namespace: {namespace}\n")
    result = await load_episodes(all_episodes)

    print(f"\n{'='*50}")
    print("BOOTSTRAP COMPLETE")
    print(f"  Loaded:  {result['loaded']}")
    print(f"  Skipped: {result['skipped']} (duplicates)")
    print(f"  Errors:  {result['errors']}")
    print(f"{'='*50}")
    print(f"\nMonitor processing: curl {BORG_URL}/admin/queue")


if __name__ == "__main__":
    ns = sys.argv[1] if len(sys.argv) > 1 else "default"
    src = None
    if "--source" in sys.argv:
        idx = sys.argv.index("--source")
        if idx + 1 < len(sys.argv):
            src = sys.argv[idx + 1]
    asyncio.run(bootstrap(ns, src))
