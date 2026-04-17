# Project Borg — Security Assessment

**Date:** 2026-03-18
**Assessed by:** Kiro CLI
**Scope:** Source code, configuration, scripts, and docs site behavior

---

## Executive Summary

The major findings from the original Kiro review are now remediated in the repository. Borg no longer relies on a default `dev-token`, MCP is no longer unauthenticated, wildcard CORS is gone, namespace authorization is enforced, docs are env-gated, unauthenticated `/health` is liveness-only, extraction is hardened, and rate limiting plus auth alerting are in place.

I do not see a remaining critical or high-severity application-code issue in the current repo state. The remaining concerns are:

- per-process rate limiting and auth-alert state in multi-replica deployments
- infrastructure controls that cannot be verified from repo code alone
- local Docker Compose database exposure that is acceptable for localhost but should not be reused blindly in shared environments

---

## Status Against Original Findings

### Remediated

- Hardcoded default authentication token
- Single static bearer token model
- Unauthenticated MCP endpoint
- Wildcard CORS
- Hardcoded DB credential defaults in active runtime paths
- Missing ingestion size limits
- Missing rate limiting
- Unauthenticated detailed `/health`
- Unprotected live docs by default
- Prompt injection risk from episode content
- Missing namespace validation
- Raw exception leakage in extraction metadata

### Still Relevant As Residual Risks

#### 1. Distributed Abuse Controls Need Shared Enforcement

- **Severity:** Medium
- **Location:** `src/borg/rate_limit.py`, `src/borg/auth.py`
- **Description:** Rate limits and repeated-auth-failure tracking are held in process memory. In multi-instance deployments, thresholds fragment by replica.

#### 2. Deployment Security Depends On Environment Controls

- **Severity:** Low
- **Location:** Out of repo scope
- **Description:** TLS termination, ingress restrictions, secret rotation, and centralized alert routing must be verified in the deployment environment.

#### 3. Local Compose Profile Exposes PostgreSQL By Design

- **Severity:** Low
- **Location:** `docker-compose.yml`
- **Description:** PostgreSQL is published for local development. That is fine for localhost workflows, but it should be removed or overridden in any shared environment.

---

## Recommended Next Steps

1. Move rate limiting and auth-alert thresholds to shared storage or the edge.
2. Wire `auth.alert` into centralized monitoring.
3. Keep Docker Compose explicitly local-only, or add a shared-environment override without published PostgreSQL ports.
4. Validate HTTPS-only ingress and secret-managed configuration in the deployment target.

---

## Conclusion

The original Kiro assessment was directionally correct for the March 17 codebase, but it is no longer current for the hardened repository state on March 18. Borg’s remaining security work is operational and deployment-focused rather than app-code remediation.
