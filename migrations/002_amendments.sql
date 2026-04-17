-- Project Borg — Schema Amendments
-- Fully idempotent — safe to run on every engine startup.
-- Run after 001_initial_schema.sql

-- ========================================
-- AMENDMENT 1: Canonical Predicate Registry
-- ========================================
CREATE TABLE IF NOT EXISTS borg_predicates (
  predicate       TEXT PRIMARY KEY,
  category        TEXT NOT NULL,
  inverse         TEXT,
  description     TEXT,
  usage_count     INT DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- Seed canonical predicates (skip if already present)
INSERT INTO borg_predicates (predicate, category, inverse, description) VALUES
  ('uses', 'structural', 'used_by', 'Subject actively uses object'),
  ('used_by', 'structural', 'uses', 'Subject is used by object'),
  ('contains', 'structural', 'contained_in', 'Subject contains object as component'),
  ('contained_in', 'structural', 'contains', 'Subject is contained within object'),
  ('depends_on', 'structural', 'dependency_of', 'Subject requires object to function'),
  ('dependency_of', 'structural', 'depends_on', 'Subject is a dependency of object'),
  ('replaced_by', 'temporal', 'replaced', 'Subject was replaced by object'),
  ('replaced', 'temporal', 'replaced_by', 'Subject replaced object'),
  ('deployed_to', 'operational', 'hosts', 'Subject is deployed to object'),
  ('hosts', 'operational', 'deployed_to', 'Subject hosts object'),
  ('implements', 'structural', 'implemented_by', 'Subject implements object'),
  ('implemented_by', 'structural', 'implements', 'Subject is implemented by object'),
  ('decided', 'decisional', 'decided_by', 'Subject made decision about object'),
  ('decided_by', 'decisional', 'decided', 'Subject was decided by object'),
  ('integrates_with', 'structural', 'integrates_with', 'Bidirectional integration'),
  ('targets', 'operational', NULL, 'Subject targets object (customer/market)'),
  ('manages', 'operational', 'managed_by', 'Subject manages object'),
  ('managed_by', 'operational', 'manages', 'Subject is managed by object'),
  ('configured_with', 'operational', NULL, 'Subject is configured using object'),
  ('blocked_by', 'operational', 'blocks', 'Subject is blocked by object'),
  ('blocks', 'operational', 'blocked_by', 'Subject blocks object'),
  ('authored_by', 'structural', 'authored', 'Subject was created by object'),
  ('authored', 'structural', 'authored_by', 'Subject created object'),
  ('owns', 'structural', 'owned_by', 'Subject owns object'),
  ('owned_by', 'structural', 'owns', 'Subject is owned by object')
ON CONFLICT (predicate) DO NOTHING;

CREATE TABLE IF NOT EXISTS borg_predicate_candidates (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  predicate       TEXT NOT NULL,
  occurrences     INT DEFAULT 1,
  example_facts   UUID[],
  mapped_to       TEXT REFERENCES borg_predicates(predicate),
  created_at      TIMESTAMPTZ DEFAULT now(),
  resolved_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pred_candidates_unresolved ON borg_predicate_candidates (predicate)
  WHERE resolved_at IS NULL;

-- ========================================
-- AMENDMENT 2: Entity Resolution Conflict Tracking
-- ========================================
CREATE TABLE IF NOT EXISTS borg_resolution_conflicts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_name     TEXT NOT NULL,
  entity_type     TEXT NOT NULL,
  namespace       TEXT NOT NULL,
  candidates      JSONB NOT NULL,
  resolved        BOOLEAN DEFAULT false,
  resolution      TEXT,
  resolved_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conflicts_unresolved ON borg_resolution_conflicts (namespace)
  WHERE resolved = false;

-- ========================================
-- AMENDMENT 3: Expanded Audit Columns for Dual-Profile Classification
-- ========================================
ALTER TABLE borg_audit_log ADD COLUMN IF NOT EXISTS primary_class TEXT;
ALTER TABLE borg_audit_log ADD COLUMN IF NOT EXISTS secondary_class TEXT;
ALTER TABLE borg_audit_log ADD COLUMN IF NOT EXISTS primary_confidence FLOAT;
ALTER TABLE borg_audit_log ADD COLUMN IF NOT EXISTS secondary_confidence FLOAT;
ALTER TABLE borg_audit_log ADD COLUMN IF NOT EXISTS profiles_executed TEXT[];
ALTER TABLE borg_audit_log ADD COLUMN IF NOT EXISTS extraction_metrics JSONB;

-- ========================================
-- AMENDMENT 4: Namespace Configuration (Configurable Budgets)
-- ========================================
CREATE TABLE IF NOT EXISTS borg_namespace_config (
  namespace         TEXT PRIMARY KEY,
  hot_tier_budget   INT DEFAULT 500,
  warm_tier_budget  INT DEFAULT 3000,
  description       TEXT,
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);

-- Seed default namespace (skip if already present)
INSERT INTO borg_namespace_config (namespace, description)
VALUES ('default', 'Default namespace for general knowledge')
ON CONFLICT (namespace) DO NOTHING;

-- ========================================
-- AMENDMENT 5: Extraction Cost Tracking (Phase 1 strategy spec)
-- ========================================
CREATE TABLE IF NOT EXISTS borg_extraction_costs (
    id              BIGSERIAL PRIMARY KEY,
    namespace       TEXT NOT NULL,
    episode_id      UUID NOT NULL,
    extraction_step TEXT NOT NULL,  -- 'entities', 'facts', 'procedures', 'specific_facts'
    model           TEXT NOT NULL,
    prompt_tokens   INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_extraction_costs_namespace_created
    ON borg_extraction_costs (namespace, created_at);
