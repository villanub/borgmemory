# Borg Security Implementation Checklist

## Goals

- Use Microsoft Entra ID as the bearer-token provider for Borg.
- Keep local PostgreSQL credentials and database URLs in `.env`.
- Remove insecure token defaults and close the unauthenticated MCP path.
- Establish a rollout order that keeps local development usable while moving the app to a production-safe auth model.

## Phase 1: Foundation

- [x] Remove hardcoded `dev-token` behavior from runtime code and scripts.
- [x] Make `DATABASE_URL` and `DATABASE_URL_SYNC` env-driven in [src/borg/config.py](/Users/benj8956/Documents/Borg/src/borg/config.py).
- [x] Move docker-compose PostgreSQL password and engine DB URLs to `.env` via [docker-compose.yml](/Users/benj8956/Documents/Borg/docker-compose.yml).
- [x] Add Entra ID settings to [src/borg/config.py](/Users/benj8956/Documents/Borg/src/borg/config.py):
  - `ENTRA_TENANT_ID`
  - `ENTRA_CLIENT_ID`
  - `ENTRA_AUDIENCE`
  - optional issuer/JWKS overrides
- [x] Add env-driven CORS origins and docs toggle.
- [x] Create an auth module for Entra bearer-token validation.
- [x] Protect `/mcp` with app-layer auth, not just client conventions.

## Phase 2: REST Authorization

- [x] Replace shared-secret REST auth with Entra token validation.
- [x] Enforce read access on:
  - `POST /api/think`
  - `POST /api/recall`
- [x] Enforce write access on:
  - `POST /api/learn`
- [x] Enforce admin access on:
  - `/api/namespaces*`
  - `/api/admin/*`
- [x] Support both Entra app roles and delegated scopes when evaluating permissions.

## Phase 3: Namespace Authorization

- [x] Define how namespace access will be represented:
  - claim-based allowlist
  - server-side mapping table
  - group-to-namespace mapping
- [x] Enforce namespace-level access checks on all request paths that accept a namespace.
- [x] Add namespace format validation.

## Phase 4: Browser And Surface Hardening

- [x] Replace wildcard CORS with an explicit allowlist.
- [x] Remove automatic bearer-token injection from the docs UI.
- [x] Disable live docs/OpenAPI routes by default outside local development.
- [x] Reduce unauthenticated `/health` output to liveness-only.

## Phase 5: Abuse Controls

- [x] Add maximum size limits for episode ingestion payloads.
- [x] Add rate limiting for:
  - `learn`
  - `think`
  - `admin`
  - `/mcp`
- [x] Add auth-failure logging.
- [x] Add basic alertability for repeated auth failures.

## Phase 6: Graph Integrity And Data Handling

- [x] Harden extraction prompts against instruction-following from episode content.
- [x] Add validation/review guardrails for extracted facts and procedures.
- [x] Remove prompt/response previews from standard logs.
- [x] Stop storing raw exception strings in episode metadata.

## Phase 7: Documentation And Verification

- [x] Update `.env.example` for the new Entra and local Postgres configuration model.
- [x] Update [README.md](/Users/benj8956/Documents/Borg/README.md) to remove `dev-token` examples.
- [x] Update scripts that send bearer tokens to expect an Entra access token from the environment.
- [x] Add tests for:
  - unauthenticated `/mcp` rejection
  - REST role enforcement
  - namespace validation
  - oversized ingestion rejection
  - docs disabled outside local development

## Rollout Order

1. Land config cleanup and Entra auth scaffolding.
2. Protect MCP and REST with Entra validation.
3. Remove `dev-token` references from scripts and docs.
4. Add REST role enforcement.
5. Add namespace authorization.
6. Add CORS/docs hardening.
7. Add abuse controls and integrity protections.

## Current Turn

- [x] Add checklist file
- [x] Refactor env-driven DB and auth configuration
- [x] Add Entra auth scaffold
- [x] Wire REST and MCP to the new auth path
- [x] Remove hardcoded token injection from the site and scripts
- [x] Start migrating MCP from the legacy SDK wrapper to FastMCP 3.x
- [x] Add env/config surface for MCP OAuth proxying via Entra
- [x] Add per-surface rate limiting and auth-failure logging
- [x] Remove prompt/response previews and sanitize stored extraction errors
- [x] Add regression coverage for unauthenticated `/mcp` rejection and docs-disabled mode
