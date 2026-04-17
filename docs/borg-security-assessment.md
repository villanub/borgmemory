# Project Borg — Security Assessment & Residual Risk Plan

**Date:** 2026-03-18
**Scope:** Current repository state for `/src/borg/`, local deployment files, scripts, and docs site behavior
**Classification:** Internal

---

## Executive Summary

The major application-security gaps identified in the earlier March 17 assessment have been remediated in the codebase. Borg now enforces Microsoft Entra authentication across REST and MCP, separates read/write/admin permissions, applies namespace authorization, gates live docs, limits unauthenticated health output, adds rate limiting and auth alerting, hardens extraction against hostile episode content, minimizes audit spillover, and enforces trusted hosts.

At this point, I do not see a remaining critical or high-severity application-code issue in the repository. The residual concerns are operational:

- rate limiting and auth-alert thresholds are still per process
- edge and infrastructure controls are not verifiable from repo code alone
- the default Compose stack still exposes PostgreSQL for local development convenience

---

## Current Status

### Completed Hardening

- Entra bearer-token validation replaced the old static `dev-token` model.
- `/mcp` now has app-layer auth and Entra-backed OAuth discovery.
- REST routes enforce read, write, and admin permissions.
- Namespace format validation and namespace authorization are enforced.
- CORS is env-driven and explicit rather than wildcard-based.
- `/docs`, `/redoc`, and `/openapi.json` are gated by `BORG_ENABLE_DOCS`.
- Unauthenticated `/health` is liveness-only; detailed metrics are admin-only.
- Ingestion payload size limits are enforced.
- Per-surface rate limiting exists for `think`, `learn`, `admin`, and `/mcp`.
- Auth failures are logged, and repeated failures emit alerts.
- Extraction prompts explicitly reject instruction-following from episode content.
- Fact and procedure extraction now uses validation and review guardrails.
- Prompt/response previews and raw exception strings were removed from secondary logging sinks.
- Compiler audit records now use hashed query fingerprints and minimized item payloads.
- Trusted host enforcement is configured via `BORG_TRUSTED_HOSTS`.
- The docs site self-hosts Swagger UI assets and disables persisted browser auth.

### Residual Findings

#### R1 — Distributed Abuse Controls Still Need Shared Enforcement

- Severity: Medium
- Location:
  - `src/borg/rate_limit.py`
  - `src/borg/auth.py`
- Impact:
  - Multi-instance deployments will fragment rate limits and repeated-auth-failure thresholds.
- Recommended action:
  - Move these controls to shared state or to the edge tier.
  - Forward `auth.alert` events to centralized monitoring.

#### R2 — Infrastructure Controls Must Be Verified Outside Repo Code

- Severity: Low
- Location:
  - Deployment environment, ingress, monitoring, and secret management
- Impact:
  - The app can still be deployed unsafely if TLS, ingress restrictions, and secret handling are weak.
- Recommended action:
  - Verify HTTPS-only ingress, network restrictions, secret-managed config, and alert routing in the target environment.

#### R3 — Compose Database Exposure Is Local-Only by Convention

- Severity: Low
- Location:
  - `docker-compose.yml`
  - `.env.example`
- Impact:
  - Reusing the local profile in a shared environment could expose PostgreSQL more broadly than intended.
- Recommended action:
  - Keep the published database port only in local development or remove it in shared overrides.

---

## Updated Priority Matrix

| Priority | Item | Effort | Action |
|----------|------|--------|--------|
| P1 | Shared/edge rate limiting | 2-6 hrs | Move throttling out of process memory |
| P1 | Centralize auth alerts | 1-2 hrs | Route `auth.alert` to monitoring |
| P2 | Deployment verification | 1-2 hrs | Validate TLS, ingress, secrets, and alert wiring |
| P3 | Local compose isolation | 30 min | Remove or override DB port publication outside localhost workflows |

---

## Summary

The earlier critical findings around MCP authentication, static auth, wildcard CORS, docs exposure, and health leakage are no longer current in repo code. Borg’s remaining security work is mainly operational hardening for shared or production environments rather than application-code remediation.
