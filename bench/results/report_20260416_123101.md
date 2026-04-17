# Borg Benchmark Report

Generated: 2026-04-16T13:06:05
Run: 20260416_123101

Tasks evaluated: 10
Total runs: 30

---

## Per-Task Results

| Task | Cond | Success | Precision | Stale | Irrelevant | Coverage | Tokens | Latency |
|------|------|---------|-----------|-------|------------|----------|--------|---------|
| task-01 | A | 0 | 0.100 | 0.000 | 0.800 | 0.200 | 0 | 62475ms |
| task-01 | B | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 3596 | 33285ms |
| task-01 | C | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 3055 | 47099ms |
| task-02 | A | 0 | 0.000 | 0.000 | 0.800 | 0.100 | 0 | 59862ms |
| task-02 | B | 0 | 0.600 | 0.200 | 0.050 | 0.600 | 2271 | 48644ms |
| task-02 | C | 1 | 0.850 | 0.200 | 0.100 | 0.950 | 2793 | 49342ms |
| task-03 | A | 0 | 0.000 | 0.000 | 0.900 | 0.000 | 0 | 52436ms |
| task-03 | B | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 2501 | 15458ms |
| task-03 | C | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 3054 | 14024ms |
| task-04 | A | 0 | 0.000 | 0.000 | 1.000 | 0.000 | 0 | 51715ms |
| task-04 | B | 1 | 0.950 | 0.050 | 0.050 | 0.950 | 3078 | 40974ms |
| task-04 | C | 1 | 0.750 | 0.050 | 0.100 | 0.500 | 3024 | 40533ms |
| task-05 | A | 0 | 0.100 | 0.000 | 0.600 | 0.100 | 0 | 92403ms |
| task-05 | B | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 3915 | 26431ms |
| task-05 | C | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 3057 | 43310ms |
| task-06 | A | 0 | 0.000 | 0.000 | 0.950 | 0.000 | 0 | 47413ms |
| task-06 | B | 0 | 0.050 | 0.900 | 0.900 | 0.050 | 2945 | 26616ms |
| task-06 | C | 1 | 0.850 | 0.000 | 0.100 | 0.900 | 3042 | 39849ms |
| task-07 | A | 0 | 0.150 | 0.000 | 0.200 | 0.200 | 0 | 36212ms |
| task-07 | B | 1 | 0.800 | 0.000 | 0.000 | 0.600 | 2186 | 35872ms |
| task-07 | C | 1 | 0.900 | 0.000 | 0.050 | 0.900 | 3071 | 63587ms |
| task-08 | A | 0 | 0.000 | 0.000 | 1.000 | 0.000 | 0 | 52938ms |
| task-08 | B | 1 | 0.850 | 0.000 | 0.000 | 0.670 | 2036 | 20783ms |
| task-08 | C | 1 | 1.000 | 0.000 | 0.000 | 1.000 | 3061 | 23380ms |
| task-09 | A | 0 | 0.250 | 0.000 | 0.300 | 0.250 | 0 | 76241ms |
| task-09 | B | 1 | 0.950 | 0.000 | 0.100 | 1.000 | 3596 | 49195ms |
| task-09 | C | 1 | 0.830 | 0.000 | 0.000 | 0.830 | 3062 | 53042ms |
| task-10 | A | 0 | 0.000 | 0.000 | 0.400 | 0.000 | 0 | 49595ms |
| task-10 | B | 1 | 0.900 | 0.000 | 0.050 | 0.950 | 1932 | 30627ms |
| task-10 | C | 1 | 0.950 | 0.000 | 0.100 | 1.000 | 3036 | 33745ms |

---

## Aggregate Metrics

| Metric | A (No Memory) | B (Simple RAG) | C (Borg Compiled) | C vs B Delta |
|--------|---------------|----------------|--------------------|--------------| 
| Task Success Rate | 0 | 0.800 | 1 | +25.0% |
| Retrieval Precision | 0.060 | 0.810 | 0.913 | +12.7% |
| Stale Fact Rate | 0.000 | 0.115 | 0.025 | -78.3% |
| Irrelevant Rate | 0.695 | 0.115 | 0.045 | -60.9% |
| Knowledge Coverage | 0.085 | 0.782 | 0.908 | +16.1% |
| Avg Context Tokens | 0 | 2805.600 | 3025.500 | +7.8% |
| Avg Latency (ms) | 58129 | 32788.500 | 40791.100 | +24.4% |

---

## Decision Gate

| Criterion | Threshold | Actual | Pass |
|-----------|-----------|--------|------|
| Precision improvement (C vs B) | ≥15% | +12.7% | ❌ |
| Token reduction (C vs B) | ≥30% reduction | +7.8% | ❌ |
| Task success non-regression | C ≥ B | 1 vs 0.800 | ✅ |

### Verdict: **STOP** — Borg compiled (C) does not outperform simple retrieval (B). Thesis disproven.

---

## Evaluation Reasoning

### task-01

**Condition A:**
- Task Success: The response did not diagnose the specific fazure-mcp incident or state the investigation findings; it only provided generic explanations and a checklist and asked for more data.
- Retrieval Precision: While the reply correctly described general 502 causes and useful diagnostics, it failed to retrieve or state the incident-specific facts (backend health metrics, Http5xx=0, FailedRequests spike, expected 403s).
- Stale Fact: The response contained general, up-to-date diagnostic information and no incorrect or outdated facts.
- Irrelevant: A large portion of the reply was generic background, checklists, and remediation guidance that do not answer the posed question about the specific fazure-mcp 502 findings.
- Knowledge Coverage: The response covered general 502 semantics and diagnostics but omitted the critical incident findings: backend remained healthy (HealthyHostCount=1, UnhealthyHostCount=0), App Service Http5xx=0, FailedRequests spike indicating transient upstream unavailability, and 403s being expected VpnOnly blocks.

**Condition B:**
- Task Success: The response correctly identifies transient backend unavailability caused by App Service restarts on a single-worker instance and the overly long App Gateway probe interval, matching the ground truth conclusion.
- Retrieval Precision: The response accurately reports HealthyHostCount=1, UnhealthyHostCount=0, Http5xx=0, FailedRequests spikes, the 300s probe interval, manual restart timestamps, and single-worker configuration as found in the evidence.
- Stale Fact: All facts align with the provided investigation context and are current to the incident timeline; no outdated information was used.
- Irrelevant: All details in the response are pertinent to diagnosing the 502s; the certificate renewal note was correctly marked as non-causal and contextual rather than irrelevant filler.
- Knowledge Coverage: The response covers the expected points: transient upstream unavailability, backend health metrics staying healthy, zero backend 5xx, FailedRequests spike, and concurrent 403s being expected VpnOnly blocks, plus appropriate remediation steps.

**Condition C:**
- Task Success: The response correctly concluded the 502s were transient gateway→backend connectivity issues (not WAF or backend 500s) and cited the supporting metrics and logs.
- Retrieval Precision: The response accurately reported HealthyHostCount=1/UnhealthyHostCount=0, Http5xx=0, FailedRequests spikes, clustered 502 windows, expected VpnOnly 403s, and included the DNS/cert and restart facts from the context.
- Stale Fact: All referenced facts align with the provided 2026-04-15 investigation details and there is no outdated or time-sensitive mismatch.
- Irrelevant: All included details (metrics, log findings, DNS/cert issue, manual restart) are relevant to diagnosing the 502s and mapping root cause contributors.
- Knowledge Coverage: The response demonstrated awareness that 502s were transient upstream unavailability, backend health stayed healthy, App Service returned no 5xx, FailedRequests spiked without health-state change, and 403s were expected VpnOnly blocks.

### task-02

**Condition A:**
- Task Success: The response gives a general Event Grid remediation pattern but fails to describe the specific azr-compliance-v3 backend-mediated flow, Fleet/APIM interaction, endpoints, and polling behavior required by the task.
- Retrieval Precision: None of the expected specifics (POST /api/event-grid/remediation/ensure, ClientSecretCredential acquisition, APIM endpoint, statusUrl polling, Fleet permission limitation) are present.
- Stale Fact: The response contains generally accurate, current Azure remediation concepts and commands; no outdated facts were identified.
- Irrelevant: Most content is generic remediation architecture and troubleshooting guidance rather than the requested implementation details for azr-compliance-v3, so much of it is not directly relevant.
- Knowledge Coverage: Covers general Event Grid remediation concepts but none of the expected specific points about azr-compliance-v3 and Fleet/APIM interactions; overall coverage is minimal.

**Condition B:**
- Task Success: The response describes the overall architecture and bulk flow well but fails to state the key backend-mediated change precisely (missing/incorrect details about the backend endpoint and authentication). It misstates the auth mechanism and omits the backend POST /api/event-grid/remediation/ensure as described in the ground truth.
- Retrieval Precision: Many implementation details are correct (bulk tables, 15s worker, polling statusUrl, APIM subscription path), but the authentication claim (Rackspace identity token) and omission of the backend ensure endpoint reduce precision.
- Stale Fact: Most facts align with the codebase, but at least one asserted design (using Rackspace identity tokens forwarded by the backend) contradicts the documented ClientSecretCredential/app-permission approach and appears outdated or incorrect.
- Irrelevant: Almost all content pertains to the remediation architecture; only minor inventory/filtering details are slightly peripheral to the core Event Grid remediation flow.
- Knowledge Coverage: The response covers the switch to backend orchestration, bulk vs targeted flows, persistence, and polling, but fails to explicitly note Fleet's required application permission and the backend's ClientSecretCredential-based token acquisition and the POST /api/event-grid/remediation/ensure backend endpoint.

**Condition C:**
- Task Success: The response accurately describes the architecture and flow (backend-mediated ensure operation, POST /api/event-grid/remediation/ensure, polling a statusUrl, APIM endpoint, and bulk-run persistence and worker behavior) and explains why the switch from browser to backend was made.
- Retrieval Precision: Most technical details match the expected knowledge, including endpoints, polling behavior, APIM path and bulk processing; however the response diverges on the exact token acquisition mechanism (claims a Rackspace identity flow rather than the ClientSecretCredential scoped to the Fleet APIM audience).
- Stale Fact: One notable factual inaccuracy is the described token acquisition approach (RACKSPACE_USERNAME/PASSWORD identity flow) which conflicts with the expected ClientSecretCredential/Entra client-credentials approach; other facts appear current.
- Irrelevant: A few inventory-scoping and naming-filter details are more implementation-specific than required for the high-level architecture, but they remain related and not truly irrelevant.
- Knowledge Coverage: The response covers the critical expected points (switch to backend, browser token limitation, POST /api/event-grid/remediation/ensure, polling statusUrl, APIM endpoint path, bulk endpoints/tables/worker and UI polling), missing only the precise stated token acquisition mechanism.

### task-03

**Condition A:**
- Task Success: The response did not retrieve or state the actual decision about SyncEventGrid scoping; it provided general recommendations instead of the specific implementation details asked for.
- Retrieval Precision: None of the required factual elements (the join to lighthouse_delegations, filters on managed_by_tenant_id and delegation_state, or the shared Lighthouse credential behavior) were present in the response.
- Stale Fact: The response made general, up-to-date recommendations and did not assert any outdated facts about the SyncEventGrid decision.
- Irrelevant: The majority of the response consisted of broad Event Grid ownership and operational guidance unrelated to the specific question about how SyncEventGrid filters to Rackspace-owned subscriptions.
- Knowledge Coverage: It failed to include any of the expected knowledge points: the customer_subscriptions join to lighthouse_delegations, managed_by_tenant_id and delegation_state filters, and the single shared Rackspace Lighthouse credential with no per-customer tokens.

**Condition B:**
- Task Success: The response accurately states that SyncEventGrid scopes to Rackspace-managed monitoring subscriptions via a join to lighthouse_delegations with managed_by_tenant_id and delegation_state filters, and that it uses a single Lighthouse credential without per-customer tokens.
- Retrieval Precision: All required details from the ground truth are present and correctly described, including the specific join, tenant check, delegation_state values, and credential behavior.
- Stale Fact: The response reflects the most recent described changes and contains no outdated assertions compared to the provided context.
- Irrelevant: All included details (ownership classifier, pre-upsert filtering, sync stats, and query alignment) are directly relevant to Event Grid scoping and ownership.
- Knowledge Coverage: The response covers joining customer_subscriptions to lighthouse_delegations, requiring managed_by_tenant_id == Rackspace Lighthouse tenant, delegation_state in active/succeeded, use of a single Lighthouse credential, and the intentional absence of per-customer tokens.

**Condition C:**
- Task Success: The response correctly states that SyncEventGrid scopes to Rackspace-managed monitoring subscriptions via a join to lighthouse_delegations, requires managed_by_tenant_id and delegation_state filters, and uses a single shared Rackspace Lighthouse credential without per-customer tokens.
- Retrieval Precision: All required specifics (join to lighthouse_delegations, managed_by_tenant_id = Rackspace Lighthouse tenant, delegation_state in active/succeeded, single shared credential, pre-upsert filtering and naming/destination patterns) are accurately and precisely reproduced.
- Stale Fact: The facts match the provided recent context (April 2026 changes) and there are no outdated or superseded statements.
- Irrelevant: All information in the response directly pertains to the scoping and ownership decision for SyncEventGrid; no unrelated details were included.
- Knowledge Coverage: The response covers the join/filter logic, exact filter values, credential usage policy, pre-upsert filtering, and related observability/query alignment as expected.

### task-04

**Condition A:**
- Task Success: The response did not describe the fleet-agent-query project requested and instead asked for clarification and provided unrelated interpretations; it fails to summarize the specified project's purpose and architecture.
- Retrieval Precision: No accurate details from the ground-truth (Azure Function, Python, intake.py, propensity_store.py, SQL protections, etc.) were retrieved or presented.
- Stale Fact: The general descriptions of FleetDM, Rancher Fleet, and Elastic Fleet are contemporary and not time-sensitive, so there are no identifiable stale facts.
- Irrelevant: Nearly all content discusses unrelated projects or asks for clarification rather than summarizing the specified fleet-agent-query codebase.
- Knowledge Coverage: None of the expected knowledge points (sales propensity reports, matching vendor solutions to Rackspace Azure fleet, Azure Function in Python, intake.py/OpenAI, propensity_store.py, SQL injection protection) were mentioned.

**Condition B:**
- Task Success: The response clearly explains what fleet-agent-query does (sales propensity reports matching vendor solutions to the Rackspace Azure managed fleet) and describes its architecture and implementation as a Python Azure Function app with intake, scoring, DB pool, and reporting components.
- Retrieval Precision: Most technical details align with the ground truth and provided context (Azure Functions in Python, OpenAI-based intake, propensity_store/customer billing queries, DB pool patterns, SQL safety and retry/backoff). Only minor specifics (e.g., exact credential class referenced) differ from some alignment notes.
- Stale Fact: The response is up-to-date with the supplied episodes; a small discrepancy exists around the precise credential class phrasing (ManagedIdentityCredential vs DefaultAzureCredential mention), but factual drift is minimal.
- Irrelevant: Nearly all content is relevant to purpose and architecture; a few extra implementation minutiae (e.g., exact package versions or storage split behavior) are additional detail but still pertinent.
- Knowledge Coverage: Covers the expected knowledge points: propensity reports, matching vendor solutions to the managed fleet, Python Azure Function architecture, intake via OpenAI, propensity_store/DB queries, and SQL/OData sanitization; coverage is comprehensive with only minor omissions in exact naming/phrasing.

**Condition C:**
- Task Success: The response accurately summarizes the purpose (sales propensity reports matching vendor solutions to the Rackspace Azure fleet) and the high-level architecture (Python Azure Function, DB-backed scoring, OpenAI integration). However it omits explicit mention of the intake.py and propensity_store.py modules and SQL injection protection details required by the ground truth.
- Retrieval Precision: Many technical details are correct and aligned with the project (Azure Functions in Python, OpenAI usage, PostgreSQL/PgBouncer patterns, managed identity auth), but some specifics (exact package versions, Python 3.12 target, Responses API fallback details) are either unverified or extraneous, and the response missed naming key modules and the safe_table_name SQL protection.
- Stale Fact: Most claims are about architecture and implementation which are not time-sensitive; only a few items (specific SDK versions or newer API patterns) could be outdated or speculative.
- Irrelevant: The reply includes some extra implementation minutiae (exact Python version, package pinning, detailed auth token refresh intervals) that are not essential to the requested high-level summary, though they remain related.
- Knowledge Coverage: Covers the core expected points: generates sales propensity reports, matches vendor solutions to the managed fleet, built as a Python Azure Function, and uses OpenAI; it fails to explicitly mention intake.py, propensity_store.py, and the SQL injection protection (safe_table_name) from the expected knowledge.

### task-05

**Condition A:**
- Task Success: The response failed to identify the actual investigation path and root cause from the ground truth (Datadog blob logs and missing topic-scoped permissions) and instead described an unrelated Log Analytics/Key Vault rotation scenario.
- Retrieval Precision: It roughly addresses generic diagnostic steps but misses all critical specifics: the Datadog blob storage location, the exact storage account/container, the five pim-dev endpoints and their request counts, and the namespace permission detail.
- Stale Fact: The response does not present outdated facts; its errors are incorrect/inapplicable to the provided ground truth rather than being stale.
- Irrelevant: Many described steps (Log Analytics queries, AppInsights correlation, Key Vault rotation remediation, AAD checks) are generic and not tied to the actual investigation path; these details are largely irrelevant given the real trace used Datadog blob logs.
- Knowledge Coverage: Covers only the high-level idea of checking logs and auth methods, but fails to cover the concrete expected items (ddlogstorage3a0c161f2e70, insights-logs-operationallogs, ServiceBus Client hitting five pim-dev endpoints with ~442-450 attempts each, and namespace-only RootManageSharedAccessKey).

**Condition B:**
- Task Success: The response correctly identified the root cause (a client using a topic-scoped SAS without Manage rights performing GetSubscription management calls) and described the investigation path from Datadog blob operational logs to the implicated app configuration.
- Retrieval Precision: All key facts from the ground truth were accurately reproduced: storage account and container, tracking ID and event time, ServiceBus Client caller, five pim-dev endpoints, ~442–450 attempts each, and the SAS permissions mismatch (Listen/Send but no Manage).
- Stale Fact: This assessment describes a specific incident and investigation details that are not time-sensitive or outdated in the provided context.
- Irrelevant: The response stayed focused on the investigation steps, evidence, root cause, and remediation; no unrelated information was introduced.
- Knowledge Coverage: The response covered all expected knowledge points: Datadog blob storage location, exact storage account/container, client and endpoints involved, request volumes, and the namespace/topic auth rule details, plus appropriate remediation suggestions.

**Condition C:**
- Task Success: The response correctly identified the investigation path (raw Datadog-forwarded blob logs), located the tracking ID and failed Retrieve Subscription events, quantified repeated attempts across five pim-dev endpoints, and attributed the 40100 errors to a client using an entity SAS without Manage rights.
- Retrieval Precision: The reply included the storage account, insights-logs-operationallogs location, tracking ID, event time, Caller, Via URI, the five affected endpoints, approximate per-endpoint attempt counts, and precise auth-rule details matching the ground truth.
- Stale Fact: All facts reference the incident on 2026-04-15 and align with the provided context; no outdated information was introduced.
- Irrelevant: All content is directly relevant to the root-cause and investigation steps; no extraneous details were added.
- Knowledge Coverage: The response covered every expected point: logs in Datadog blob storage (not Log Analytics), exact storage account and log container, ServiceBus Client caller against the five pim-dev endpoints, ~442–450 attempts per endpoint, and namespace auth rules lacking topic-scoped Manage permission.

### task-06

**Condition A:**
- Task Success: The response did not describe the actual fazure-mcp implementation; it provided a generic Azure authentication architecture rather than the specific configuration and rules for fazure-mcp.
- Retrieval Precision: None of the expected specific facts were present (no mention of Application Gateway with WAF, the waf-appgw policy and VpnOnly rule, AllowTrustedVpnFazureMcp, the Janus AWS IPs, the azure-mcp-prod App Service, or that 403s are expected).
- Stale Fact: The response offered general, up-to-date architectural recommendations rather than asserting any specific, potentially outdated facts about fazure-mcp.
- Irrelevant: Most content is generic reference architecture and implementation guidance that does not answer the task-specific question about fazure-mcp's actual authentication and network access controls.
- Knowledge Coverage: The response failed to cover any of the expected knowledge items listed for fazure-mcp (App Gateway/WAF rules, allowlist IPs, backend App Service, and expected 403 behavior).

**Condition B:**
- Task Success: The response does not describe the Application Gateway/WAF protection, the VpnOnly rule, the AllowTrustedVpnFazureMcp rule, the required Janus AWS IP allowlist, or the named App Service backend; instead it fabricates an APIM-centric model that contradicts the ground truth.
- Retrieval Precision: Most technical details are incorrect or unsupported (APIM tri-auth, DDI header, subscription key, Rackspace X-Auth-Token mappings); there is essentially no precise retrieval of the documented WAF rules or allowlisted IP addresses.
- Stale Fact: The reply introduces many invented/incorrect facts about APIM behavior and header mappings that are not in the provided context and appear misleading rather than merely outdated.
- Irrelevant: The answer focuses on APIM-specific authentication flows and header-based RBAC which are not relevant to the expected WAF/AGW allowlist and VpnOnly enforcement details.
- Knowledge Coverage: It fails to cover the core expected items (Application Gateway with WAF, VpnOnly rule, AllowTrustedVpnFazureMcp rule, Janus AWS IPs, azure-mcp-prod App Service, and expected 403 behavior); coverage is nearly zero.

**Condition C:**
- Task Success: The response correctly describes the primary authentication and access control architecture: an Application Gateway with a WAF policy protecting the App Service (azure-mcp-prod) and the use of VPN/allow‑list rules (including Janus AWS IPs) to permit trusted traffic.
- Retrieval Precision: Most named components and rules match the ground truth (per‑site WAF policy, VpnOnly, AllowTrustedVpnFazureMcp, explicit Janus IP allow‑listing, backend App Service). A few extra specifics (e.g., an additional global WAF name, oauth host, probe path) are plausible but not present in the ground truth and may be inferred.
- Stale Fact: No information appears to be time‑sensitive or outdated; the response aligns with the provided ground truth rather than legacy data.
- Irrelevant: Most content is on‑topic; minor extra details (OAuth host name, probe path, RateLimit mention) go beyond the core task but remain related to access/authentication context.
- Knowledge Coverage: The response includes the key expected points (Application Gateway with WAF, waf-appgw-phoenix-prod-southcentralus-rax-fazure-mcp-sites, VpnOnly rule, AllowTrustedVpnFazureMcp, explicit Janus IP allow‑listing, backend azure-mcp-prod). It omits an explicit note that 403s from unknown/external IPs are expected/correct and does not mention the resource group (rg-azure-mcp-prod).

### task-07

**Condition A:**
- Task Success: The response failed to retrieve or state the specific implementation change (call to janus_helpers.get_rackspace_identity_token(auth_mode='identity') and sending the token as Authorization: Bearer to APIM) and instead provided speculative reasons rather than the documented decision.
- Retrieval Precision: The reply correctly identified a move to Rackspace Identity in general and offered plausible rationale, but it did not cite the exact code change, function call, auth parameters (RACKSPACE_USERNAME/PASSWORD), or the Authorization: Bearer usage required by the ground truth.
- Stale Fact: The content is speculative and general rather than time-sensitive; there are no outdated facts presented.
- Irrelevant: Most of the speculative reasons are relevant to possible motivations for the change, but several paragraphs add broader operational speculation that goes beyond the specific, requested retrieval.
- Knowledge Coverage: The response captures the high-level shift away from Entra to Rackspace Identity, but it omits key expected details: the exact helper call (get_rackspace_identity_token(auth_mode='identity')), use of RACKSPACE_USERNAME/PASSWORD, and that the token is sent as Authorization: Bearer to APIM.

**Condition B:**
- Task Success: The response correctly states the decision to switch to the Rackspace Identity flow and gives the core rationale for the change (reuse of existing flow, APIM compatibility, and reduced operational complexity).
- Retrieval Precision: The response accurately lists key reasons and mentions RACKSPACE_USERNAME/PASSWORD and APIM validation, but it omits the specific implementation detail that code now calls shared.janus_helpers.get_rackspace_identity_token(auth_mode='identity') and that the token is explicitly sent as Authorization: Bearer to APIM.
- Stale Fact: All facts align with the provided context and there are no outdated or contradicted statements.
- Irrelevant: The reply stays on-topic and focuses on the decision and rationale without introducing unrelated information.
- Knowledge Coverage: The response covers avoiding Entra client credentials, use of Rackspace credentials, APIM compatibility, and the x-tenant-id limitation, but it fails to mention the exact function call (get_rackspace_identity_token with auth_mode='identity') and the explicit Authorization: Bearer header usage.

**Condition C:**
- Task Success: The response correctly identifies the switch from Entra client credentials to the Rackspace Identity flow and gives the primary rationale (reuse of existing flow) required by the task.
- Retrieval Precision: The reply accurately cites shared.janus_helpers.get_rackspace_identity_token(auth_mode='identity') and the use of Rackspace credentials, and explains APIM acceptance reasons; it omits one explicit detail about sending the token as Authorization: Bearer to the APIM Event Grid ensure endpoint.
- Stale Fact: All facts align with the provided recent context (2026-04-09 change) and no outdated information is introduced.
- Irrelevant: Most content is directly relevant; a small portion (claims about prior Entra brittleness in prod) goes beyond the minimal ground-truth rationale but remains plausibly related.
- Knowledge Coverage: Covers the key points (move away from Entra, use Rackspace Identity, call to janus_helpers, RACKSPACE env vars, APIM validation rationale) but misses explicitly stating the token is sent as 'Authorization: Bearer' to the APIM Event Grid ensure endpoint.

### task-08

**Condition A:**
- Task Success: The response failed to state the actual root cause or the concrete fix for the fleet-platform-app pip-audit failure; it returned a generic remediation workflow instead of the specific facts requested.
- Retrieval Precision: None of the expected, specific facts (aiohttp pinned to 3.13.3, pip-audit 10 GHSA advisories, updated to 3.13.4, 454 tests passing, Rackspace SAML blocking GH Actions) were returned; the reply gave generic, mostly Node/npm-focused steps.
- Stale Fact: The response did not present time-sensitive factual claims about the incident, so there are no outdated facts to rate.
- Irrelevant: The content is largely irrelevant: it discusses general audit workflows and npm/yarn commands rather than the Python/pip-audit/aiohttp-specific root cause and fix requested.
- Knowledge Coverage: None of the expected knowledge items (aiohttp versions, affected files, number of advisories, test results, or CI gating cause) were included.

**Condition B:**
- Task Success: The response identifies the root cause (aiohttp pinned to 3.13.3 in both requirement files) and the fix (updated to aiohttp==3.13.4), and verifies remediation with pip-audit and the test run.
- Retrieval Precision: Most key facts are correct (affected files, vulnerable version, fixed version, pip-audit/no-vulns, 454 tests passed). It omitted the explicit count of 10 GHSA advisories and did not mention the Rackspace SAML blockage that caused the CI gate to be triggered locally.
- Stale Fact: All reported facts align with the provided ground truth and there is no evidence of outdated information.
- Irrelevant: All included details are relevant to the root cause and remediation of the CI security-audit failure; none are extraneous.
- Knowledge Coverage: Covers most expected points (pinned version, affected manifests, first fixed version, manifests updated, pip-audit clean, tests passed) but misses the precise count of 10 GHSA advisories and the CI trigger cause (Rackspace SAML blocking of the gh token).

**Condition C:**
- Task Success: The response correctly identifies the root cause, the affected files, the number of advisories and first fixed version, the manifest updates, and verification steps including pip-audit and pytest results.
- Retrieval Precision: All specific facts from the ground truth are accurately reported (aiohttp 3.13.3 in both requirements, 10 GHSA advisories, first fixed in 3.13.4, updated to 3.13.4, pip-audit clean, 454 pytest passed).
- Stale Fact: No information is outdated or contradicted by the provided context; all facts align with the most recent entries.
- Irrelevant: The response contains only pertinent details about the failure, fix, verification, and relevant pipeline change (removal of Safety).
- Knowledge Coverage: The reply covers every expected knowledge point listed in the prompt, including the CI gate trigger cause (SAML blocking) implicitly acknowledged by noting local reproduction and pipeline simplification.

### task-09

**Condition A:**
- Task Success: The response provides a thorough generic layered debugging workflow but does not return the specific procedural pattern for fazure-mcp (named logs, exact commands like show-backend-health, App Gateway metrics, or the expected VpnOnly 403 behavior).
- Retrieval Precision: The reply covers many relevant debugging concepts (WAF, health probes, ingress, packet capture, Azure Network Watcher) but fails to retrieve the exact artifacts and checks required by the task (AGWAccessLogs, AGWFirewallLogs, show-backend-health, HealthyHostCount/UnhealthyHostCount, azure-mcp-prod App Insights, VpnOnly 403 note).
- Stale Fact: Content is general, current, and contains no identifiable outdated or incorrect factual claims.
- Irrelevant: Some sections (deep generic Kubernetes and service-mesh checks, broad RCA/process details) are useful but exceed the concise, targeted runbook pattern requested and thus are partially extraneous.
- Knowledge Coverage: Covers high-level telemetry collection and layered isolation principles and mentions WAF and Azure tooling, but omits several key, task-specific checks and named logs/metrics that constitute the established fazure-mcp debugging pattern.

**Condition B:**
- Task Success: The response clearly presents a repeatable, step-by-step debugging pattern that matches the requested procedure for fazure-mcp connectivity/auth issues, including AGW access + firewall logs, App Service checks, App Gateway metrics, and App Insights correlation.
- Retrieval Precision: Most expected items are present and accurately described (AGWAccessLogs, AGWFirewallLogs, App Service state and show-backend-health, HealthyHostCount/UnhealthyHostCount, App Insights), with only minor extra operational recommendations beyond the minimal pattern.
- Stale Fact: The response contains procedural and observational guidance without time-sensitive factual claims, so no stale information is present.
- Irrelevant: A small portion of the reply expands into broader hardening and ASE/scm/backend network details that, while useful, are slightly beyond the concise debugging pattern requested.
- Knowledge Coverage: All key expected knowledge points are covered explicitly: starting with AGW access logs, checking WAF logs, verifying App Service state and backend health, inspecting App Gateway metrics, looking at App Insights, and noting expected VpnOnly 403s.

**Condition C:**
- Task Success: The response captures the established debugging pattern for fazure-mcp, covering AGW access/firewall logs, backend health checks, App Service/App Insights correlation, and VPN/Janus IP allowlisting, so it meets the task goal.
- Retrieval Precision: Most expected items are present (AGWAccessLogs, AGWFirewallLogs, App Service/App Insights, WAF rule inspection, VPN/Janus allowlists), but it omits an explicit mention of App Gateway metrics names (HealthyHostCount/UnhealthyHostCount) and the specific show-backend-health command.
- Stale Fact: The response contains no outdated timestamps or superseded facts from the provided context and stays procedural and current.
- Irrelevant: All included items are relevant to debugging fazure-mcp traffic/auth issues; there is no off-topic content.
- Knowledge Coverage: Coverage is high—access logs, firewall logs, backend health, App Insights, and expected 403 behavior are addressed—but it lacks explicit reference to App Gateway metric names (HealthyHostCount/UnhealthyHostCount) and a direct callout to show-backend-health, so not fully exhaustive.

### task-10

**Condition A:**
- Task Success: The response failed to provide the specific implementation details requested for azr-compliance-v3 and instead gave generic architecture patterns rather than the concrete behaviors and artifacts described in the ground truth.
- Retrieval Precision: None of the expected specific facts (dedicated Postgres tables, ProcessEventGridBulkRemediation 15s timer worker, requeue behavior, recency index, separate fleet env knobs) were retrieved or mentioned.
- Stale Fact: The response contained general, current best-practice patterns and no incorrect or outdated statements about azr-compliance-v3; it simply lacked the specific facts.
- Irrelevant: Much of the content is generic architecture guidance that is somewhat related but not directly answering the specific implementation question; several paragraphs and checks were outside the requested scope.
- Knowledge Coverage: The expected knowledge points (dedicated tables, timer worker interval, non-reuse of sync_queue, requeueing stale items, recency index, and separate fleet knobs) were not covered at all.

**Condition B:**
- Task Success: The response accurately describes the bulk remediation architecture, including dedicated Postgres tables, the 15s ProcessEventGridBulkRemediation timer worker, not reusing sync_queue, restart recovery by requeuing stale items, and worker-specific Fleet knobs.
- Retrieval Precision: Most facts are stated precisely (tables, timer worker, advisory lock, requeue behavior, recency indexing, Fleet knobs), but the exact recency index column specification (run_id, updated_at DESC, id DESC) was not quoted verbatim.
- Stale Fact: The content aligns with the provided ground truth and recent context; there are no outdated or incorrect claims.
- Irrelevant: Nearly all details are relevant to architecture and recovery; minor UI/UX wording and extra phrasing add little architecture value but are not truly irrelevant.
- Knowledge Coverage: Covers the required concepts (dedicated tables, 15s timer worker, no sync_queue reuse, requeueing stale items, recency-based polling, and Fleet polling knobs); only the specific index column ordering was omitted.

**Condition C:**
- Task Success: The response correctly describes the dedicated Postgres tables, the 15s ProcessEventGridBulkRemediation timer worker, avoidance of sync_queue, snapshotting behavior, persisted per-item status, recovery of stale runs, recency-based polling, and separate Fleet polling knobs, matching the task requirements.
- Retrieval Precision: Most factual details from the ground truth are present and accurate; the only minor omission is not quoting the exact recency index tuple (run_id, updated_at DESC, id DESC) verbatim, though it does state a recency index/polling ordering exists.
- Stale Fact: No facts presented conflict with the provided ground truth or context; details are current and consistent with the implementation notes.
- Irrelevant: A small amount of extra detail about Fleet/API auth flows is peripheral to the core architecture question but not incorrect.
- Knowledge Coverage: All expected knowledge points (tables, worker cadence and lock, non-reuse of sync_queue, stale-item requeue behavior, recency-based polling, and separate worker knobs) are covered.
