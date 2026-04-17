# Borg OSS strip-down — design spec

**Date:** 2026-04-17
**Target repo:** `https://github.com/villanub/borgmemory`
**Working dir:** `/Users/benj8956/Documents/Borg-OSS/Borg`

## Goal

Produce a public, Apache-2.0 OSS distribution of Borg that contains only the Basic tier — single-user, local, no auth — by hard-stripping all Teams and Enterprise code paths, docs, site content, and internal strategy documents. Initialize a fresh git repo and push to `villanub/borgmemory`.

## Approach

**Hard strip, not gated.** Delete Teams/Enterprise files outright and remove their imports from shared modules. Collapse the remaining auth surface to a no-auth local stub. Do not leave a runtime tier/profile flag — there is only one tier now.

## Scope

### 1. Files to delete

| Path | Why |
|---|---|
| `src/borg/auth_teams.py` | Teams API-key auth module |
| `src/borg/api/admin_keys.py` | Teams admin endpoints for key management |
| `tests/test_auth_teams.py` | Teams auth tests |
| `tests/test_mcp_auth.py` | MCP bearer-auth tests (Teams/Enterprise only) |
| `migrations/003_namespace_group_access.sql` | Enterprise RBAC schema |
| `migrations/004_api_keys.sql` | Teams API-key schema |
| `docker-compose.teams.yml` | Teams compose file |
| `.env.teams.example` | Teams env template |
| `docs/getting-started-teams.md` | Teams docs |
| `docs/superpowers/specs/2026-04-15-borg-tiering-design.md` | Internal tiering strategy — not for public repo |
| `docs/superpowers/specs/2026-04-16-borg-strategy-and-differentiation.md` | Internal strategy — not for public repo |

### 2. Code edits

- **`src/borg/main.py`** — remove `auth_teams` and `admin_keys` imports and any route/router registrations they provide.
- **`src/borg/api/__init__.py`** — drop the `admin_keys` router inclusion.
- **`src/borg/mcp/__init__.py`** — remove API-key / bearer-auth branches.
- **`src/borg/auth.py`** — collapse to a minimal no-auth passthrough; no token validation.
- **`src/borg/config.py`** — remove tier/profile switching and Teams/Enterprise env vars.
- **`src/borg/extraction/pipeline.py`**, **`src/borg/extraction/embed.py`** — remove API-key / namespace-group branches.
- **`bootstrap/loader.py`** — remove `ENTRA_ACCESS_TOKEN` usage; call the local engine without a bearer token.
- **`cli/borg_cli.py`** — remove the `--token` option and its "Teams/Enterprise" label text.
- **`install.sh`** — change "Self-hosted AI memory for your team" banner to OSS tagline; swap `racker/borg` → `villanub/borgmemory` in install URL.
- **`pyproject.toml`** — strip any Teams-only entries (if present).
- **`.env`** — remove Teams/Enterprise secrets; leave Basic vars (`OPENAI_API_KEY`, DB URL, etc.).
- **`bench/config.py`** — drop `ENTRA_ACCESS_TOKEN` / `BORG_AUTH_TOKEN` usage; benchmark runs against local engine with no auth.
- **`bench/seed.py`** — same; remove the "Set ENTRA_ACCESS_TOKEN" gate.
- **`bench/run.sh`** — remove the `az login` / Entra token-fetching preamble; the script should just `docker compose up -d` (if needed) and run the benchmark against `localhost:8080`.
- **`bench/tasks.json`** — stays as-is. The Entra / Rackspace references inside task content are example Azure infrastructure questions, not auth config; they are part of the benchmark scenarios.

### 3. Docs + README

- **`README.md`** — delete the tier comparison table; replace license/tier section with a single paragraph ("Apache 2.0, single-user, local"). Remove the Teams getting-started link. Swap `racker/borg` → `villanub/borgmemory` in install curl command.
- **`docs/user-guide.md`**, **`docs/borg-v2-1-current.md`** — strip tier references; keep Basic-only flow.
- **Rename** `docs/getting-started-basic.md` → `docs/getting-started.md` (no "basic" qualifier needed with one tier). Update README link accordingly.

### 4. Site updates

Edit the following to remove tier comparison content, "Teams coming soon" / "Contact us for Enterprise" CTAs, and swap all repo URLs to `villanub/borgmemory`:

- `site/src/app/page.tsx` (landing)
- `site/src/app/features/page.tsx`
- `site/src/app/integrations/page.tsx`
- `site/src/app/architecture/page.tsx`
- `site/src/app/science/page.tsx`
- `site/src/app/benchmarks/page.tsx`
- `site/src/app/docs/page.tsx`
- `site/src/components/Nav.tsx`
- `site/src/components/Footer.tsx`

Do **not** rebuild `site/out/` locally — it is gitignored and the existing `.github/workflows/deploy-site.yml` runs `npm run build` on push to main.

### 5. .gitignore + .env

Update `.gitignore`:

- Remove `.env.teams` and `.env.basic` lines (only `.env` remains).
- Remove `bench/results/` line — these files ship with the OSS repo as reproducibility evidence.
- Keep `.local/`, `.remember/`, `.claude/`, `.codex/`, `.kiro/`, `node_modules/`, `site/.next/`, `site/out/`, `.venv/` ignored.

### 6. Git init + push

Since `/Users/benj8956/Documents/Borg-OSS/Borg` is not currently a git repo, and `villanub/borgmemory` already exists on GitHub:

1. `git init` in the working directory (default branch `main`).
2. Verify `.gitignore` excludes `.venv/`, `node_modules/`, `.local/`, `.remember/`, `.claude/`, and `.env`, so secrets and vendor dirs do not get committed.
3. `git add .` + single initial commit with message `Initial commit — Borg OSS`.
4. `git remote add origin https://github.com/villanub/borgmemory.git`.
5. `git push -u origin main`.

## Out of scope

- Deleting / archiving the old `racker/borg` repo — user will handle directly in GitHub UI.
- CI pipeline other than the existing `deploy-site.yml`.
- License file changes — Apache 2.0 remains.
- Kiro integration in `cli/borg_cli.py` — kiro is a client, not a tier feature; stays as-is.
- Benchmark source code changes — `bench/` has no Teams/Enterprise code paths; only mentions of tiers in `bench/results/report.md` prose will be updated if present.

## Verification plan

After code changes but before `git push`:

1. `grep -ri "auth_teams\|admin_keys\|ENTRA_ACCESS_TOKEN\|BORG_AUTH_TOKEN\|namespace_group" --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=bench/results --exclude-dir=.git .` returns zero matches. ("teams" / "enterprise" / "entra" prose may still legitimately appear in `bench/tasks.json` scenario content — those are not auth artifacts and stay.)
2. `grep -r "racker/borg" --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git .` returns zero matches.
3. `python -c "from src.borg.main import app"` imports cleanly (no broken imports from deleted modules).
4. `pytest tests/ -x` passes with the remaining tests (`test_api`, `test_auth_basic`, `test_cli`, `test_integration_cli`, `test_security_hardening`).
5. `git status` before the initial commit shows no `.env`, `.venv/`, `node_modules/`, `.local/`, `.remember/`, or `.claude/` entries staged.

## Risk notes

- **Import cascade:** stripping `auth_teams` may expose call sites in `main.py`, `api/__init__.py`, `mcp/__init__.py` that need tidying. The implementation plan must handle this iteratively — run imports after each strip.
- **Test removal side-effects:** `test_mcp_auth.py` and `test_auth_teams.py` may share fixtures with `test_api.py` / `test_auth_basic.py`. Grep for shared fixtures before deleting.
- **.env may contain live secrets** — confirm `.env` is in `.gitignore` before `git add` to avoid leaking to the public repo.
