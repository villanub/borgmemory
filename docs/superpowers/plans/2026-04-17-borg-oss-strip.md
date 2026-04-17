# Borg OSS strip-down Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a public OSS (Apache-2.0) distribution of Borg containing only the Basic tier — single-user, local, no auth — by hard-stripping Teams/Enterprise code, updating docs and site, and pushing to `https://github.com/villanub/borgmemory`.

**Architecture:** Hard strip of Teams/Enterprise modules, deletions of tier-specific files, collapse of profile-switching code to Basic-only paths. No runtime tier flag retained.

**Tech Stack:** Python 3.12 (FastAPI, asyncpg, pgvector), Next.js site, Docker Compose, pytest, git.

**Spec:** `docs/superpowers/specs/2026-04-17-borg-oss-strip-design.md`

**Working directory:** `/Users/benj8956/Documents/Borg-OSS/Borg` (not currently a git repo).

---

## Task 1: Delete Teams/Enterprise files

**Files:**
- Delete: `src/borg/auth_teams.py`
- Delete: `src/borg/api/admin_keys.py`
- Delete: `tests/test_auth_teams.py`
- Delete: `tests/test_mcp_auth.py`
- Delete: `migrations/003_namespace_group_access.sql`
- Delete: `migrations/004_api_keys.sql`
- Delete: `docker-compose.teams.yml`
- Delete: `.env.teams.example`
- Delete: `docs/getting-started-teams.md`
- Delete: `docs/superpowers/specs/2026-04-15-borg-tiering-design.md`
- Delete: `docs/superpowers/specs/2026-04-16-borg-strategy-and-differentiation.md`

- [ ] **Step 1: Remove the files**

```bash
rm src/borg/auth_teams.py \
   src/borg/api/admin_keys.py \
   tests/test_auth_teams.py \
   tests/test_mcp_auth.py \
   migrations/003_namespace_group_access.sql \
   migrations/004_api_keys.sql \
   docker-compose.teams.yml \
   .env.teams.example \
   docs/getting-started-teams.md \
   docs/superpowers/specs/2026-04-15-borg-tiering-design.md \
   docs/superpowers/specs/2026-04-16-borg-strategy-and-differentiation.md
```

- [ ] **Step 2: Verify**

Run: `ls src/borg/auth_teams.py src/borg/api/admin_keys.py 2>&1`
Expected: both report `No such file or directory`.

- [ ] **Step 3: Do not commit yet** — the repo isn't initialized. Deletions accumulate for the initial commit in Task 14.

---

## Task 2: Collapse `src/borg/config.py` to Basic-only

**Files:**
- Modify: `src/borg/config.py` (full rewrite to Basic-only)

**Context:** Current file has `borg_profile = "enterprise"`, Entra fields, Teams admin key, and many computed properties derived from Entra settings. Target: a small Settings class with only DB URL, OpenAI keys, and operational knobs.

- [ ] **Step 1: Rewrite the file**

Replace the entire contents of `src/borg/config.py` with:

```python
"""Borg configuration via environment variables."""

from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., description="Async PostgreSQL connection string")
    database_url_sync: str = Field(..., description="Sync PostgreSQL connection string")

    # OpenAI (OSS Borg supports standard OpenAI or Azure OpenAI)
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    # Optional Azure OpenAI (leave empty to use standard OpenAI)
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_embedding_endpoint: str = ""
    azure_openai_embedding_api_key: str = ""
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_extraction_deployment: str = "gpt-5-mini"

    # App surface
    borg_public_base_url: str = "http://localhost:8080"
    borg_enable_docs: bool = True
    borg_cors_origins: str = ""
    borg_trusted_hosts: str = ""
    borg_max_episode_content_chars: int = 20000
    borg_max_episode_metadata_bytes: int = 16000
    borg_max_episode_participants: int = 25
    borg_rate_limit_think_per_minute: int = 30
    borg_rate_limit_learn_per_minute: int = 60
    borg_rate_limit_admin_per_minute: int = 10
    borg_rate_limit_mcp_per_minute: int = 60
    borg_extraction_procedure_min_confidence: float = 0.6

    # Compiler defaults
    default_namespace: str = "default"
    hot_tier_token_budget: int = 500
    warm_tier_token_budget: int = 3000
    max_candidates: int = 20
    max_graph_hops: int = 2

    # Logging
    log_level: str = "INFO"

    @property
    def borg_cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.borg_cors_origins.split(",") if origin.strip()]

    @property
    def borg_trusted_hosts_list(self) -> list[str]:
        if self.borg_trusted_hosts:
            return [host.strip() for host in self.borg_trusted_hosts.split(",") if host.strip()]
        trusted_hosts = {"localhost", "127.0.0.1", "[::1]", "testserver"}
        parsed = urlparse(self.borg_public_base_url_value)
        if parsed.hostname:
            trusted_hosts.add(parsed.hostname)
        return sorted(trusted_hosts)

    @property
    def borg_public_base_url_value(self) -> str:
        return self.borg_public_base_url.rstrip("/")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
```

- [ ] **Step 2: Verify imports succeed after later task changes**

After Task 3 (auth rewrite), run:

```bash
.venv/bin/python -c "from borg.config import settings; print(settings.default_namespace)"
```

Expected: prints `default` or the value from `.env`.

---

## Task 3: Collapse `src/borg/auth.py` to no-auth passthrough

**Files:**
- Modify: `src/borg/auth.py` (full rewrite — drop Entra/JWT, return local principal everywhere)

**Context:** Current file is 632 lines of Entra JWT handling. OSS Basic has no auth, so every dependency function just returns a fully-permissioned local principal.

- [ ] **Step 1: Rewrite the file**

Replace the entire contents of `src/borg/auth.py` with:

```python
"""Authentication passthrough for OSS Borg — single-user, local, no auth."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Header
from starlette.types import ASGIApp, Receive, Scope, Send

from borg.namespaces import normalize_namespace


@dataclass(frozen=True)
class Principal:
    subject: str
    object_id: str | None
    name: str | None
    permissions: frozenset[str]
    claims: dict[str, Any]


def _local_principal() -> Principal:
    return Principal(
        subject="local",
        object_id=None,
        name="local-user",
        permissions=frozenset({"read", "write", "admin"}),
        claims={},
    )


async def require_namespace_access(namespace: str, **_: Any) -> str:
    return normalize_namespace(namespace)


def require_permissions(_required: set[str] | None = None):
    async def dependency(
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> Principal:
        return _local_principal()

    return dependency


async def require_authenticated() -> Principal:
    return _local_principal()


async def require_read_access() -> Principal:
    return _local_principal()


async def require_write_access() -> Principal:
    return _local_principal()


async def require_admin_access() -> Principal:
    return _local_principal()


def build_fastmcp_auth_provider():
    return None


def mcp_require_permissions(_required: set[str] | None = None):
    return lambda _ctx: True


class EntraBearerAuthMiddleware:
    """Compatibility middleware — OSS has no auth; this passes through unchanged."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            scope["borg_principal"] = _local_principal()
        await self.app(scope, receive, send)
```

- [ ] **Step 2: Verify imports**

```bash
.venv/bin/python -c "from borg.auth import require_read_access, Principal; print('ok')"
```

Expected: prints `ok`.

---

## Task 4: Strip teams/enterprise from `main.py`, `api/__init__.py`, `mcp/__init__.py`

**Files:**
- Modify: `src/borg/main.py`
- Modify: `src/borg/api/__init__.py`
- Modify: `src/borg/mcp/__init__.py`

- [ ] **Step 1: Inspect and edit each file**

For each file, open it and remove:

- Imports of `borg.auth_teams` or `borg.api.admin_keys` (module-level imports or lazy imports inside functions).
- Router registrations that include the deleted `admin_keys` module.
- Any `if settings.borg_profile == "teams":` / `== "enterprise":` branches; keep only the code that would run for `basic`.
- Any remaining references to `settings.borg_profile`, `settings.entra_*`, `settings.borg_admin_key`.

Because the exact line numbers depend on the current file contents, open each file with Read first, then make targeted Edits.

- [ ] **Step 2: Verify the FastAPI app imports**

```bash
.venv/bin/python -c "from borg.main import app; print([r.path for r in app.routes][:5])"
```

Expected: prints a list of route paths with no errors.

- [ ] **Step 3: Verify the MCP app imports**

```bash
.venv/bin/python -c "import borg.mcp; print('ok')"
```

Expected: prints `ok`.

---

## Task 5: Strip teams/enterprise from extraction pipeline

**Files:**
- Modify: `src/borg/extraction/pipeline.py`
- Modify: `src/borg/extraction/embed.py`

- [ ] **Step 1: Read both files and remove tier branches**

Remove any `if settings.borg_profile == ...` conditionals, API-key lookups, and namespace-group checks. Keep only the Basic code path (single-user, unrestricted namespace access).

- [ ] **Step 2: Verify**

```bash
.venv/bin/python -c "from borg.extraction import pipeline, embed; print('ok')"
```

Expected: prints `ok`.

---

## Task 6: Update `bootstrap/loader.py` and `cli/borg_cli.py`

**Files:**
- Modify: `bootstrap/loader.py`
- Modify: `cli/borg_cli.py`

- [ ] **Step 1: `bootstrap/loader.py` — drop ENTRA_ACCESS_TOKEN**

Edit the top of `bootstrap/loader.py`. Replace:

```python
BORG_URL = "http://localhost:8080/api"
BORG_TOKEN = os.getenv("ENTRA_ACCESS_TOKEN", "")
```

with:

```python
BORG_URL = "http://localhost:8080/api"
```

Then remove the two places that reference `BORG_TOKEN`:

In `load_episodes`, change:

```python
resp = await client.post(
    f"{BORG_URL}/learn",
    json=ep,
    headers={"Authorization": f"Bearer {BORG_TOKEN}"},
)
```

to:

```python
resp = await client.post(f"{BORG_URL}/learn", json=ep)
```

In `bootstrap`, remove the preamble:

```python
if not BORG_TOKEN:
    raise RuntimeError("Set ENTRA_ACCESS_TOKEN to a Microsoft Entra access token")
```

And in the final monitor hint line, replace:

```python
print(f"\nMonitor processing: curl -H 'Authorization: Bearer {BORG_TOKEN}' {BORG_URL}/admin/queue")
```

with:

```python
print(f"\nMonitor processing: curl {BORG_URL}/admin/queue")
```

Also remove the unused `import os`.

- [ ] **Step 2: `cli/borg_cli.py` — drop `--token` option**

In the `bootstrap` click command, remove the `--token` option:

Delete these lines:

```python
@click.option(
    "--token",
    default=None,
    help="Bearer token for authentication (Teams/Enterprise).",
)
```

Change the function signature from:

```python
def bootstrap(
    docs_dir: str,
    namespace: str,
    borg_url: str,
    source: str,
    dry_run: bool,
    token: str | None,
) -> None:
```

to:

```python
def bootstrap(
    docs_dir: str,
    namespace: str,
    borg_url: str,
    source: str,
    dry_run: bool,
) -> None:
```

And replace:

```python
headers: dict[str, str] = {"Content-Type": "application/json"}
if token:
    headers["Authorization"] = f"Bearer {token}"
```

with:

```python
headers: dict[str, str] = {"Content-Type": "application/json"}
```

- [ ] **Step 3: Verify CLI imports and runs**

```bash
.venv/bin/borg --help
.venv/bin/borg bootstrap --help
```

Expected: help text prints with no mention of `--token`, no import errors.

---

## Task 7: Update `bench/` scripts

**Files:**
- Modify: `bench/config.py`
- Modify: `bench/seed.py`
- Modify: `bench/run.sh`

- [ ] **Step 1: `bench/config.py` — drop auth tokens**

Find the line:

```python
self.borg_token = os.getenv("ENTRA_ACCESS_TOKEN", os.getenv("BORG_AUTH_TOKEN", ""))
```

Delete it. Then search the rest of `bench/config.py` and `bench/runner.py` for any use of `self.borg_token` or `borg_token` and remove those (most likely an `Authorization` header in an httpx call).

- [ ] **Step 2: `bench/seed.py` — drop the token gate**

Find and delete the block around line 304:

```python
if not <token var>:
    print("ERROR: Set ENTRA_ACCESS_TOKEN or BORG_AUTH_TOKEN before running the seeder.")
    sys.exit(1)
```

And any `Authorization: Bearer` header set in seed.py's httpx calls.

- [ ] **Step 3: `bench/run.sh` — remove Entra preamble**

Replace the entire file contents with:

```bash
#!/usr/bin/env bash
# Borg benchmark runner — executes the full suite against a local Borg engine.
#
# Usage:
#   ./bench/run.sh                      # Full A/B/C run
#   ./bench/run.sh --condition C        # Condition C only
#   ./bench/run.sh --task task-01       # Single task
#   ./bench/run.sh --report             # Regenerate latest report only
#
# Prerequisites:
#   - Docker stack running:  docker compose up -d
#   - .venv activated or run from repo root
#   - OPENAI_API_KEY set in .env

set -euo pipefail
cd "$(dirname "$0")/.."

# Load .env
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

# Activate venv if not already active
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  source .venv/bin/activate
fi

# Connectivity check (skip for --report since it doesn't hit the engine)
if [[ "${1:-}" != "--report" ]]; then
  STATUS=$(curl -sf "${BORG_PUBLIC_BASE_URL:-http://localhost:8080}/health" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" \
    2>/dev/null || echo "unreachable")
  if [[ "$STATUS" != "ok" ]]; then
    echo "ERROR: Borg engine not reachable at ${BORG_PUBLIC_BASE_URL:-http://localhost:8080}"
    echo "Start it with: docker compose up -d"
    exit 1
  fi
  echo "Borg engine: $STATUS"
  echo ""
fi

python -m bench.runner "$@"
```

- [ ] **Step 4: Verify**

```bash
grep -n "ENTRA\|BORG_AUTH_TOKEN\|borg_token" bench/*.py bench/*.sh
```

Expected: no matches (or only matches inside `bench/tasks.json` scenario content, which is OK — that file is scenario text, not config).

---

## Task 8: Update `install.sh`

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Update the banner**

Replace:

```
│           Self-hosted AI memory for your team          │
```

with:

```
│         Self-hosted AI memory for your projects        │
```

- [ ] **Step 2: Replace repo URLs**

Search `install.sh` for `racker/borg` and replace every occurrence with `villanub/borgmemory`.

- [ ] **Step 3: Verify**

```bash
grep -n "racker/borg\|for your team" install.sh
```

Expected: no matches.

---

## Task 9: Update README and docs

**Files:**
- Modify: `README.md`
- Modify: `docs/user-guide.md`
- Modify: `docs/borg-v2-1-current.md`
- Rename: `docs/getting-started-basic.md` → `docs/getting-started.md`

- [ ] **Step 1: Rename the getting-started doc**

```bash
mv docs/getting-started-basic.md docs/getting-started.md
```

- [ ] **Step 2: README.md — replace tier table**

Open `README.md`. Replace the curl URL:

```
curl -fsSL https://raw.githubusercontent.com/racker/borg/main/install.sh | sh
```

with:

```
curl -fsSL https://raw.githubusercontent.com/villanub/borgmemory/main/install.sh | sh
```

Replace the entire "Tiers" section (starting at `## Tiers` through the table) with:

```markdown
## License

Borg is open source under the Apache 2.0 license. Single-user, local, no auth — run it on your workstation or a VM you control.
```

Replace the "Documentation" section links block:

```markdown
## Documentation

- [Getting Started](docs/getting-started.md) — Local single-user setup in 3 commands
- [Architecture](docs/borg-v2-1-current.md) — Engine design, compiler pipeline, offline worker
- [Benchmark Details](bench/results/report.md) — Full per-task results and evaluation reasoning
```

Replace the License section at the bottom with:

```markdown
## License

Apache 2.0. See `LICENSE` for details.
```

- [ ] **Step 3: docs/user-guide.md, docs/borg-v2-1-current.md — strip tier references**

Read each file and remove any section that describes Teams or Enterprise features, or that compares tiers. Keep only descriptions of Basic (single-user, local) behavior.

- [ ] **Step 4: Verify**

```bash
grep -ni "teams\|enterprise\|racker/borg" README.md docs/user-guide.md docs/borg-v2-1-current.md docs/getting-started.md
```

Expected: zero matches.

---

## Task 10: Update site pages

**Files:**
- Modify: `site/src/app/page.tsx`
- Modify: `site/src/app/features/page.tsx`
- Modify: `site/src/app/integrations/page.tsx`
- Modify: `site/src/app/architecture/page.tsx`
- Modify: `site/src/app/science/page.tsx`
- Modify: `site/src/app/benchmarks/page.tsx`
- Modify: `site/src/app/docs/page.tsx`
- Modify: `site/src/components/Nav.tsx`
- Modify: `site/src/components/Footer.tsx`

- [ ] **Step 1: For each file, remove tier references and swap repo URLs**

In each file:

- Delete any JSX section that renders a tier comparison table or "Teams coming soon" / "Contact us for Enterprise" CTA.
- Replace every `racker/borg` string with `villanub/borgmemory`.
- Replace any `benjamin.villanueva@rackspace.com` contact-for-enterprise mention with an open-source-appropriate mention (e.g. the GitHub Issues URL `https://github.com/villanub/borgmemory/issues`).

Read each file first to locate the relevant JSX. Use targeted Edits.

- [ ] **Step 2: Verify**

```bash
grep -rn "racker/borg\|Teams\|Enterprise\|tier" site/src/
```

Expected: no matches except possibly prose using the word "tier" in a non-commercial sense (e.g. "hot tier / warm tier" in compiler context — those stay).

- [ ] **Step 3: Build site locally to catch TSX errors**

```bash
cd site && npm run build && cd ..
```

Expected: `npm run build` completes with no errors. (The `site/out/` output remains gitignored — CI will rebuild on push.)

---

## Task 11: Update `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Remove lines**

Remove these lines from `.gitignore`:

```
.env.basic
.env.teams
```

(The line `.env` stays — we don't commit secrets.)

Remove this line:

```
# Benchmark results (generated data)
bench/results/
```

(The user wants bench/results/ committed as reproducibility evidence.)

- [ ] **Step 2: Verify**

```bash
grep -n "\.env\.basic\|\.env\.teams\|bench/results" .gitignore
```

Expected: no matches.

---

## Task 12: Review `.env` contents

**Files:**
- Review (no edit required unless secrets found): `.env`
- Create if missing: `.env.example`

- [ ] **Step 1: Confirm `.env` is gitignored**

```bash
grep -n "^\.env$" .gitignore
```

Expected: one match on a line by itself.

- [ ] **Step 2: Read `.env` and check for Teams/Enterprise-specific keys**

Open `.env`. If there are Entra or admin-key entries (`ENTRA_*`, `BORG_ADMIN_KEY`, `BORG_AUTH_TOKEN`), remove them. They are not needed for Basic.

- [ ] **Step 3: Create `.env.example` for OSS users**

Write to `.env.example`:

```
# PostgreSQL connection (with pgvector extension enabled)
DATABASE_URL=postgresql+asyncpg://borg:borg@localhost:5432/borg
DATABASE_URL_SYNC=postgresql+psycopg2://borg:borg@localhost:5432/borg

# OpenAI (required)
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini

# Optional: Azure OpenAI (leave empty to use standard OpenAI)
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=

# App surface
BORG_PUBLIC_BASE_URL=http://localhost:8080
BORG_ENABLE_DOCS=true
LOG_LEVEL=INFO
```

- [ ] **Step 4: Verify**

```bash
test -f .env.example && echo "exists"
grep -n "^\.env\.example$" .gitignore || echo "not ignored — good"
```

Expected: `exists` and `not ignored — good`.

---

## Task 13: Run verification suite

- [ ] **Step 1: Import smoke test**

```bash
.venv/bin/python -c "from borg.main import app; from borg.auth import require_read_access; from borg.config import settings; print('imports ok')"
```

Expected: `imports ok`.

- [ ] **Step 2: Grep for removed symbols**

```bash
grep -ri "auth_teams\|admin_keys\|ENTRA_ACCESS_TOKEN\|BORG_AUTH_TOKEN\|namespace_group" \
  --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=bench/results --exclude-dir=.git .
```

Expected: zero matches.

- [ ] **Step 3: Grep for old repo URL**

```bash
grep -rn "racker/borg" --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git .
```

Expected: zero matches.

- [ ] **Step 4: Run remaining tests**

```bash
.venv/bin/pytest tests/ -x
```

Expected: all tests pass. If any test fails due to stale fixtures referencing deleted modules, fix the fixture or delete the obsolete test.

- [ ] **Step 5: Ruff lint**

```bash
.venv/bin/ruff check .
```

Expected: zero errors. Fix any import/unused-variable issues caused by the strip.

---

## Task 14: Git init and push to `villanub/borgmemory`

- [ ] **Step 1: Confirm `.env` and secrets are gitignored**

```bash
grep -E "^\.env$|^\.venv/$|^\.local/|^\.remember/|^\.claude/|^node_modules/" .gitignore
```

Expected: matches for all. If anything is missing, add it before proceeding.

- [ ] **Step 2: Initialize git with `main` as default branch**

```bash
git init -b main
```

Expected: `Initialized empty Git repository in .../Borg/.git/`.

- [ ] **Step 3: Stage and review what will be committed**

```bash
git add .
git status | head -50
```

Check the staged list for any leaked secrets: no `.env`, `.venv/`, `node_modules/`, `.local/`, `.remember/`, `.claude/` should appear. If any do, stop, update `.gitignore`, then `git reset` and restart this step.

- [ ] **Step 4: Initial commit**

```bash
git commit -m "Initial commit — Borg OSS

Public Apache-2.0 release of Borg: a PostgreSQL-native memory
compiler for AI coding agents. Single-user, local, no auth.
"
```

Expected: commit succeeds with a summary of files.

- [ ] **Step 5: Add the remote and push**

```bash
git remote add origin https://github.com/villanub/borgmemory.git
git push -u origin main
```

Expected: push succeeds. If the remote rejects because it already has commits (e.g. a README was created when the repo was made), run `git pull --rebase origin main` then push again.

- [ ] **Step 6: Verify on GitHub**

```bash
gh repo view villanub/borgmemory --web
```

Expected: the repo page opens in the browser showing the pushed contents.
