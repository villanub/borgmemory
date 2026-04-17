"""Benchmark data seeder — creates synthetic episodes covering all 10 benchmark tasks.

Generates realistic episodes that, once processed by the offline pipeline, will
produce the entities, facts, and procedures expected by the benchmark evaluation.

Usage:
    python -m bench.seed              # Seed and wait for processing
    python -m bench.seed --no-wait    # Seed without waiting
"""

import asyncio
import sys
import time

import httpx

from bench.config import cfg

BORG_URL = cfg.borg_url
NAMESPACE = cfg.namespace

# Synthetic episodes covering the 10 benchmark tasks.
# Each episode is written as a realistic conversation excerpt or decision record
# that the extraction pipeline can process into entities, facts, and procedures.
SEED_EPISODES = [
    # ── Task 1: APIM service token retry ──
    {
        "content": (
            "Debugging the APIM service token retry issue. Root cause identified: "
            "the service token contains special XML characters that break when injected "
            "directly into the APIM policy XML. The retry loop was infinite because the "
            "token validation kept failing on the malformed XML. Solution: URL-encode the "
            "service token before injecting it into the policy XML body. Tested with DDI "
            "tenant isolation headers and confirmed the fix works across all three auth paths "
            "in the tri-auth pattern."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "debug", "project": "azure-msp-platform"},
    },
    {
        "content": (
            "APIM uses a tri-auth pattern for service authentication: (1) DDI tenant "
            "isolation via x-auth-ddi header, (2) service-to-service token exchange via "
            "Azure AD app registration, and (3) subscription key for rate limiting. All "
            "three must pass for a request to be authorized. When debugging auth issues, "
            "always check DDI isolation first — it's the most common failure point because "
            "tenant context gets lost in retry loops."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "architecture", "project": "azure-msp-platform"},
    },
    {
        "content": (
            "Established debugging pattern for APIM authentication issues: Step 1 — Check "
            "DDI tenant isolation headers (x-auth-ddi) are present and correct. Step 2 — "
            "Inspect the service token for encoding issues (XML escaping, URL encoding). "
            "Step 3 — Review APIM policy XML for correct token injection points. Step 4 — "
            "Verify the subscription key is active and rate limits aren't exceeded. This "
            "pattern has been used successfully across 4 separate auth debugging sessions."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "procedure", "project": "azure-msp-platform"},
    },
    # ── Task 2: AMA v3 DCR drift detection ──
    {
        "content": (
            "Designing the AMA v3 DCR drift detection system. Key considerations: all "
            "Data Collection Rules follow the rax- prefix naming convention (e.g., "
            "rax-windows-perf, rax-linux-syslog). DCR assignment depends on OS "
            "categorization — Windows servers get different DCRs than Linux. The v2 schema "
            "had drift issues because DCR assignments weren't validated after scale events. "
            "v3 needs a reconciliation loop that compares desired state (from CMDB) against "
            "actual DCR assignments in Azure Monitor."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "architecture", "project": "ama-compliance"},
    },
    {
        "content": (
            "AMA compliance tracking v2 post-mortem: the main drift risk was that DCR "
            "assignments could silently change during Azure maintenance or subscription "
            "migrations. The rax- prefix convention helps identify Rackspace-managed DCRs "
            "vs customer-created ones. OS categorization (Windows/Linux/Other) determines "
            "which DCR set gets applied. v3 should add a daily drift scan comparing "
            "ARM resource graph state against the expected DCR mapping table."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "architecture", "project": "ama-compliance"},
    },
    # ── Task 3: SOX compliance for AI dev ──
    {
        "content": (
            "Decision: Use pgAudit for SOX compliance on all Borg database tables. "
            "Rationale: pgAudit is natively supported on Azure PostgreSQL Flexible Server, "
            "requires no additional licensing, and generates audit logs that satisfy SOX "
            "Section 404 requirements for change tracking and access control evidence. "
            "All production changes to AI systems require approval gates — no direct "
            "commits to main branch without PR review."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "compliance", "project": "borg"},
    },
    {
        "content": (
            "SOX compliance review for AI development practices at Rackspace. Key outcomes: "
            "(1) All AI model deployments must go through the existing change management "
            "process with CAB approval. (2) Database audit trails must capture who changed "
            "what and when — pgAudit handles this for PostgreSQL workloads. (3) AI training "
            "data must have provenance tracking — Borg's episode source_episodes array "
            "satisfies this requirement. (4) Approval gates are required at three stages: "
            "code review, staging validation, and production deployment."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "compliance", "project": "azure-msp-platform"},
    },
    # ── Task 4: Cyber Recovery value proposition ──
    {
        "content": (
            "Cyber Recovery targeting strategy: 36 customers identified across two primary "
            "segments — BFSI (banking, financial services, insurance) and Healthcare. These "
            "segments have the highest regulatory pressure for data recovery capabilities. "
            "Current pipeline: 12 BFSI customers with active RFPs, 8 Healthcare customers "
            "in discovery phase. Impact metrics from existing deployments: 99.97% recovery "
            "success rate, average RTO reduced from 72 hours to 4 hours, 60% cost reduction "
            "vs on-premise DR solutions."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "writing", "project": "cyber-recovery"},
    },
    {
        "content": (
            "Cyber Recovery value proposition elements: (1) Azure-native DR with automated "
            "failover — no manual intervention required. (2) Immutable backup vaults with "
            "ransomware protection. (3) Compliance-ready — meets HIPAA, SOC2, and PCI-DSS "
            "requirements out of the box. (4) Managed service — Rackspace handles monitoring, "
            "testing, and runbook execution. Target positioning: 'Your data recovers itself. "
            "Your team focuses on business.' Key differentiator vs competitors: integrated "
            "with existing Azure MSP management plane, single pane of glass."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "writing", "project": "cyber-recovery"},
    },
    # ── Task 5: Project Sentinel customers ──
    {
        "content": (
            "Project Sentinel architecture review. Sentinel is a multi-agent AI compliance "
            "automation system using 6 specialized agents built on Semantic Kernel and "
            "Azure AI Foundry. The agents handle: (1) policy ingestion, (2) control mapping, "
            "(3) evidence collection, (4) gap analysis, (5) remediation recommendations, "
            "(6) report generation. Currently targeting Contoso Financial, Woodgrove Bank, "
            "and Fabrikam Healthcare as pilot customers. Discussions also included Adatum "
            "Insurance and Northwind Traders for phase 2."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "architecture", "project": "sentinel"},
    },
    {
        "content": (
            "Project Sentinel customer pipeline update: Contoso Financial has signed the "
            "pilot agreement — starting with SOC2 compliance automation. Woodgrove Bank "
            "is in legal review. Fabrikam Healthcare wants HIPAA focus first, then SOC2. "
            "Adatum Insurance expressed interest but needs budget approval in Q2. Northwind "
            "Traders declined — they went with a competing solution from ServiceNow."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "compliance", "project": "sentinel"},
    },
    # ── Task 6: MFA Phase 2 ARM issue ──
    {
        "content": (
            "Resolved the MFA Phase 2 ARM template deployment issue. The problem was that "
            "the ARM template specified resource scopes that didn't align with the new MFA "
            "policy requirements. When MFA was enforced, the service principal couldn't "
            "authenticate because the ARM scope was set to subscription-level but the MFA "
            "policy required resource-group-level scope. Fix: Updated ARM scope definitions "
            "to use resource-group-level scoping. Used az rest instead of curl for the API "
            "calls because az rest handles token refresh and MFA challenges automatically, "
            "while curl required manual token management."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "debug", "project": "azure-msp-platform"},
    },
    # ── Task 7: AeroPro Texas architecture ──
    {
        "content": (
            "AeroPro Texas current architecture: Hub-spoke network topology with Azure "
            "Virtual WAN. Production workloads run in South Central US region. Key "
            "components: (1) AKS cluster for microservices (3 node pools, autoscaling), "
            "(2) Azure SQL Managed Instance for relational data, (3) Event Hubs for "
            "real-time telemetry ingestion, (4) Azure Data Factory for ETL pipelines, "
            "(5) Front Door for global load balancing with WAF. Recent decision: migrated "
            "from App Service to AKS for better container orchestration and cost control. "
            "Current spend: approximately $45K/month across all services."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "architecture", "project": "aeropro"},
    },
    {
        "content": (
            "AeroPro Texas deployment update: Added a secondary region (East US 2) for "
            "disaster recovery. Active-passive configuration with Azure Traffic Manager "
            "for DNS-based failover. Database replication via Azure SQL auto-failover groups. "
            "Blob storage uses GRS (geo-redundant storage) with RA-GRS for read access "
            "during outages. RPO target: 5 minutes. RTO target: 30 minutes."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "architecture", "project": "aeropro"},
    },
    # ── Task 8: Wisdm RFP governance automation ──
    {
        "content": (
            "Wisdm RFP preparation — governance automation section. Wisdm requires "
            "automated governance capabilities including: policy-as-code enforcement via "
            "Azure Policy, automated compliance reporting (SOC2, ISO 27001, NIST CSF), "
            "and real-time drift detection on resource configurations. Key metrics to "
            "include: 95% policy compliance rate within first 30 days of onboarding, "
            "automated remediation for 80% of common drift scenarios, compliance report "
            "generation reduced from 2 weeks manual effort to 4 hours automated."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "writing", "project": "wisdm"},
    },
    {
        "content": (
            "Wisdm governance automation technical approach: Layer 1 — Azure Policy "
            "definitions for resource compliance (naming, tagging, allowed regions, SKU "
            "restrictions). Layer 2 — Custom policy initiatives grouped by compliance "
            "framework (SOC2 controls mapped to Azure Policy). Layer 3 — Automated "
            "remediation tasks triggered by policy violations. Layer 4 — Dashboard and "
            "reporting via Azure Monitor Workbooks with scheduled PDF export for auditors."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "architecture", "project": "wisdm"},
    },
    # ── Task 9: Auth debugging patterns (procedural) ──
    # Already covered by episodes above (tasks 1 and 3)
    # Adding one more reinforcement episode
    {
        "content": (
            "Another auth debugging session today. Same pattern worked: started with DDI "
            "isolation check (x-auth-ddi header was missing due to a gateway misconfiguration), "
            "then inspected the service token (this time it was expired, not malformed), "
            "and finally reviewed the APIM policy to confirm the token injection point "
            "was correct. The DDI-first pattern continues to be the fastest path to "
            "root cause — 3 out of 4 auth issues this month were DDI-related."
        ),
        "source": "claude-code",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "debug", "project": "azure-msp-platform"},
    },
    # ── Task 10: Azure-PROD schema changes ──
    {
        "content": (
            "Azure-PROD schema change log — March 2026: (1) Added new resource group "
            "rax-prod-sentinel-rg for Project Sentinel pilot. (2) Updated NSG rules on "
            "rax-prod-apim-subnet to allow outbound to Azure AI Foundry endpoints. "
            "(3) Migrated 3 App Service plans to AKS node pools (AeroPro workloads). "
            "(4) Added Azure Monitor DCR rax-prod-sentinel-dcr for Sentinel agent telemetry. "
            "(5) Deprecated the legacy rax-prod-monitoring-rg resource group — resources "
            "moved to rax-prod-observability-rg."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "compliance", "project": "azure-msp-platform"},
    },
    {
        "content": (
            "Azure-PROD entity changes this month: New service principal created for "
            "Sentinel (sp-sentinel-prod) with contributor role scoped to rax-prod-sentinel-rg. "
            "AeroPro AKS cluster upgraded from 1.28 to 1.29. Front Door WAF policy updated "
            "to include new OWASP 3.2 ruleset. Key Vault rotation policy changed from "
            "90-day to 60-day rotation cycle for all managed certificates. These changes "
            "supersede the previous 90-day rotation convention documented in February."
        ),
        "source": "manual",
        "namespace": NAMESPACE,
        "metadata": {"session_type": "compliance", "project": "azure-msp-platform"},
    },
]


async def seed():
    """Load all seed episodes into Borg and optionally wait for processing."""
    wait = "--no-wait" not in sys.argv

    print("Borg Benchmark Seeder")
    print(f"{'=' * 50}")
    print(f"Namespace:  {NAMESPACE}")
    print(f"Episodes:   {len(SEED_EPISODES)}")
    print(f"Wait:       {wait}")
    print()

    # Check engine health
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{BORG_URL}/health")
            r.raise_for_status()
            print("Borg engine: healthy")
        except Exception as e:
            print(f"ERROR: Cannot reach Borg at {BORG_URL}: {e}")
            sys.exit(1)

    # Ensure namespace exists
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BORG_URL}/api/namespaces/{NAMESPACE}")
        if r.status_code == 404:
            print(f"Creating namespace '{NAMESPACE}'...")
            await client.post(
                f"{BORG_URL}/api/namespaces",
                json={"namespace": NAMESPACE, "description": "Azure Expert MSP platform"},
            )

    # Ingest episodes
    loaded, skipped, errors = 0, 0, 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, ep in enumerate(SEED_EPISODES, 1):
            try:
                r = await client.post(f"{BORG_URL}/api/learn", json=ep)
                result = r.json()
                status = result.get("status", "")
                if status == "duplicate":
                    skipped += 1
                    print(f"  [{i}/{len(SEED_EPISODES)}] Duplicate — skipped")
                elif status == "accepted":
                    loaded += 1
                    print(f"  [{i}/{len(SEED_EPISODES)}] Accepted — {ep['content'][:60]}...")
                else:
                    errors += 1
                    print(f"  [{i}/{len(SEED_EPISODES)}] Unexpected: {result}")
            except Exception as e:
                errors += 1
                print(f"  [{i}/{len(SEED_EPISODES)}] Error: {e}")

    print(f"\nIngestion complete: {loaded} loaded, {skipped} duplicates, {errors} errors")

    if not wait:
        print("Skipping wait — episodes will process in background.")
        return

    # Wait for processing
    print("\nWaiting for extraction pipeline to process episodes...")
    max_wait = 300  # 5 minutes
    t0 = time.time()

    while time.time() - t0 < max_wait:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{BORG_URL}/api/admin/queue")
            queue = r.json()
            depth = queue.get("queue_depth", 0)
            if depth == 0:
                break
            elapsed = int(time.time() - t0)
            print(f"  Queue depth: {depth} ({elapsed}s elapsed)", end="\r")
            await asyncio.sleep(3)

    # Final stats
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BORG_URL}/api/namespaces/{NAMESPACE}")
        ns = r.json()
        stats = ns.get("stats", {})

    print(f"\n\n{'=' * 50}")
    print(f"SEEDING COMPLETE — namespace: {NAMESPACE}")
    print(f"  Entities:   {stats.get('entities', '?')}")
    print(f"  Facts:      {stats.get('facts', '?')}")
    print(f"  Episodes:   {stats.get('episodes', '?')}")
    print(f"  Procedures: {stats.get('procedures', '?')}")
    print(f"{'=' * 50}")
    print("\nReady to run benchmarks: python -m bench.runner")


if __name__ == "__main__":
    asyncio.run(seed())
