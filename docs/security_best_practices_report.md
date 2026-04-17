# Borg Security Assessment

**Date:** 2026-03-18
**Scope:** Repository-visible application code, local deployment configuration, and docs site behavior

## Executive Summary

The major application-layer findings from the initial March 17 review are now remediated in repo code. Borg now uses Microsoft Entra bearer-token validation, role-based and namespace-scoped authorization, authenticated MCP access, explicit CORS allowlists, docs gating, liveness-only unauthenticated health checks, request-size limits, rate limiting, auth-failure logging and alerting, extraction hardening, audit-log minimization, and trusted host enforcement.

Current finding summary:
- 0 critical
- 0 high
- 1 medium
- 2 low

The remaining risks are mostly operational rather than code defects: abuse controls are still instance-local, infrastructure controls such as TLS and ingress policy are not verifiable from this repo alone, and the local Docker Compose profile still exposes PostgreSQL for convenience in single-machine development.

## Remediated Since Initial Review

- Entra-based auth replaced the old static bearer-token model.
- `/mcp` now enforces app-layer auth and OAuth discovery for supported clients.
- REST permissions are separated into read, write, and admin, with namespace authorization checks.
- Wildcard CORS was replaced with an explicit allowlist.
- Live docs are env-gated, and Swagger auth is no longer auto-persisted in the site UI.
- Unauthenticated `/health` is liveness-only; detailed metrics are limited to Borg admins.
- Ingestion size limits, rate limiting, auth-failure logging, and auth alerting are implemented.
- Extraction prompts and write-path validation now treat episode content as untrusted.
- Prompt/response previews and raw exception strings were removed from secondary logs and metadata.
- Compiler audit logs now store hashed query fingerprints and minimized item metadata.
- Trusted host enforcement is configured in the FastAPI app.
- Lingering `dev-token` helper usage was removed from active scripts, including the benchmark seeder.

## Findings

### BG-SEC-001

- Severity: Medium
- Rule IDs: abuse prevention / deployment consistency review
- Location:
  - `src/borg/rate_limit.py`
  - `src/borg/auth.py`
- Evidence:
  - Rate limiting is implemented in-process.
  - Auth-failure alert state is also held in process memory.
- Impact:
  - In a multi-replica deployment, throttling and repeated-failure thresholds fragment by instance.
  - A caller can distribute abuse across replicas and stay below each local threshold.
- Fix:
  - Move request throttling to shared storage or the edge tier.
  - Forward `auth.alert` events to centralized monitoring.
- Mitigation:
  - Keep the service behind a gateway, reverse proxy, or platform ingress that enforces shared limits.
  - Treat the in-app limiter as defense in depth for local and single-instance deployments.
- False positive notes:
  - This is not a problem for the default local single-instance workflow.

### BG-SEC-002

- Severity: Low
- Rule IDs: deployment verification / edge control review
- Location:
  - Out of repo scope
- Evidence:
  - The repository cannot verify runtime TLS termination, ingress allowlists, private networking, secret rotation policy, or centralized log/alert forwarding.
- Impact:
  - A deployment can still be unsafe if Borg is exposed without standard edge protections, even though the app code is materially hardened.
- Fix:
  - Verify HTTPS-only ingress, restricted exposure, secret management, and centralized monitoring in the target environment.
- Mitigation:
  - Document these checks in deployment runbooks and release gates.
- False positive notes:
  - This is intentionally reported as an infrastructure verification gap, not as an app-code vulnerability.

### BG-SEC-003

- Severity: Low
- Rule IDs: local development profile review
- Location:
  - `docker-compose.yml`
  - `.env.example`
- Evidence:
  - The local Compose stack still exposes PostgreSQL on `5433` and uses local development credentials from `.env`.
- Impact:
  - If the local profile is reused in a shared environment without review, the database can be exposed more broadly than intended.
- Fix:
  - Keep the published database port only in local profiles, or override it out in shared environments.
  - Use secret-managed credentials outside single-user development.
- Mitigation:
  - Treat `docker-compose.yml` as local-only infrastructure unless explicitly adapted.
- False positive notes:
  - This is a local-development tradeoff, not a production app-code flaw.

## Conclusion

Borg’s repo-visible security posture is substantially improved and no longer shows the critical or high-risk app-code issues that were present in the initial assessment. The remaining work is mostly operational: shared abuse controls, deployment verification, and keeping local-only defaults from leaking into broader environments.
