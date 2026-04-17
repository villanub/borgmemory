-- Project Borg — Initial Schema Migration
-- Fully idempotent — safe to run on every engine startup.
-- Run against PostgreSQL 14+ with pgvector extension.

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- pgaudit is optional — available on Azure PostgreSQL but not in the pgvector Docker image.
-- To enable: CREATE EXTENSION IF NOT EXISTS pgaudit;

-- ========================================
-- EPISODES (Immutable Evidence Layer)
-- ========================================
CREATE TABLE IF NOT EXISTS borg_episodes (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source          TEXT NOT NULL,
  source_id       TEXT,
  source_event_id TEXT,
  content         TEXT NOT NULL,
  content_hash    TEXT NOT NULL,
  occurred_at     TIMESTAMPTZ NOT NULL,
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  namespace       TEXT NOT NULL,
  metadata        JSONB DEFAULT '{}',
  participants    TEXT[],
  embedding       vector(1536),
  tags            TEXT[],
  processed       BOOLEAN DEFAULT false,
  deleted_at      TIMESTAMPTZ,
  deletion_reason TEXT,
  UNIQUE(source, source_event_id)
);

CREATE INDEX IF NOT EXISTS idx_episodes_embedding ON borg_episodes
  USING ivfflat (embedding vector_cosine_ops) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_episodes_ns_occurred ON borg_episodes (namespace, occurred_at DESC)
  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_episodes_hash ON borg_episodes (content_hash);
CREATE INDEX IF NOT EXISTS idx_episodes_processed ON borg_episodes (processed)
  WHERE processed = false AND deleted_at IS NULL;

-- ========================================
-- ENTITIES (Graph Nodes)
-- ========================================
CREATE TABLE IF NOT EXISTS borg_entities (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  entity_type     TEXT NOT NULL,
  namespace       TEXT NOT NULL,
  properties      JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ DEFAULT now(),
  source_episodes UUID[],
  deleted_at      TIMESTAMPTZ,
  UNIQUE(name, entity_type, namespace)
);

CREATE INDEX IF NOT EXISTS idx_entities_ns_type ON borg_entities (namespace, entity_type)
  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_entities_name ON borg_entities (namespace, name)
  WHERE deleted_at IS NULL;

-- ========================================
-- ENTITY SERVING STATE (Derived)
-- ========================================
CREATE TABLE IF NOT EXISTS borg_entity_state (
  entity_id       UUID PRIMARY KEY REFERENCES borg_entities(id),
  embedding       vector(1536),
  summary         TEXT,
  tier            TEXT DEFAULT 'warm' CHECK (tier IN ('hot', 'warm')),
  salience_score  FLOAT DEFAULT 0.5,
  access_count    INT DEFAULT 0,
  last_accessed   TIMESTAMPTZ,
  pinned          BOOLEAN DEFAULT false,
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ========================================
-- FACTS (Graph Edges — Temporal)
-- ========================================
CREATE TABLE IF NOT EXISTS borg_facts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id      UUID NOT NULL REFERENCES borg_entities(id),
  predicate       TEXT NOT NULL,
  object_id       UUID NOT NULL REFERENCES borg_entities(id),
  namespace       TEXT NOT NULL,
  valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_until     TIMESTAMPTZ,
  source_episodes UUID[] NOT NULL,
  superseded_by   UUID REFERENCES borg_facts(id),
  evidence_status TEXT NOT NULL DEFAULT 'extracted'
    CHECK (evidence_status IN (
      'user_asserted', 'observed', 'extracted', 'inferred',
      'promoted', 'deprecated', 'superseded'
    )),
  properties      JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ DEFAULT now(),
  deleted_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_facts_current ON borg_facts (namespace, subject_id)
  WHERE valid_until IS NULL AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_facts_object ON borg_facts (object_id)
  WHERE valid_until IS NULL AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_facts_status ON borg_facts (evidence_status);

-- ========================================
-- FACT SERVING STATE (Derived)
-- ========================================
CREATE TABLE IF NOT EXISTS borg_fact_state (
  fact_id         UUID PRIMARY KEY REFERENCES borg_facts(id),
  embedding       vector(1536),
  salience_score  FLOAT DEFAULT 0.5,
  access_count    INT DEFAULT 0,
  last_accessed   TIMESTAMPTZ,
  tier            TEXT DEFAULT 'warm' CHECK (tier IN ('hot', 'warm')),
  pinned          BOOLEAN DEFAULT false,
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ========================================
-- PROCEDURES (Candidate Patterns)
-- ========================================
CREATE TABLE IF NOT EXISTS borg_procedures (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pattern         TEXT NOT NULL,
  category        TEXT,
  namespace       TEXT NOT NULL,
  source_episodes UUID[] NOT NULL,
  first_observed  TIMESTAMPTZ DEFAULT now(),
  last_observed   TIMESTAMPTZ DEFAULT now(),
  observation_count INT DEFAULT 1,
  evidence_status TEXT NOT NULL DEFAULT 'extracted'
    CHECK (evidence_status IN ('extracted', 'promoted', 'deprecated')),
  confidence      FLOAT DEFAULT 0.3,
  embedding       vector(1536),
  tier            TEXT DEFAULT 'warm' CHECK (tier IN ('hot', 'warm')),
  deleted_at      TIMESTAMPTZ
);

-- ========================================
-- AUDIT LOG
-- ========================================
CREATE TABLE IF NOT EXISTS borg_audit_log (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at        TIMESTAMPTZ DEFAULT now(),
  task_class        TEXT NOT NULL,
  namespace         TEXT NOT NULL,
  query_text        TEXT,
  target_model      TEXT,
  retrieval_profile TEXT NOT NULL,
  candidates_found  INT,
  candidates_selected INT,
  candidates_rejected INT,
  selected_items    JSONB,
  rejected_items    JSONB,
  compiled_tokens   INT,
  output_format     TEXT,
  latency_total_ms  INT,
  latency_classify_ms INT,
  latency_retrieve_ms INT,
  latency_rank_ms   INT,
  latency_compile_ms INT,
  user_rating       FLOAT
);

CREATE INDEX IF NOT EXISTS idx_audit_created ON borg_audit_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_ns ON borg_audit_log (namespace, created_at DESC);

-- ========================================
-- HOT TIER SNAPSHOTS
-- ========================================
CREATE TABLE IF NOT EXISTS borg_snapshots (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot_at     TIMESTAMPTZ DEFAULT now(),
  namespace       TEXT NOT NULL,
  hot_entities    JSONB,
  hot_facts       JSONB,
  hot_procedures  JSONB,
  total_tokens    INT
);

-- ========================================
-- GRAPH TRAVERSAL FUNCTION (1-2 hop)
-- ========================================
CREATE OR REPLACE FUNCTION borg_traverse(
  p_entity_id UUID,
  p_max_hops INT DEFAULT 2,
  p_namespace TEXT DEFAULT 'default'
) RETURNS TABLE (
  entity_id UUID, entity_name TEXT, entity_type TEXT,
  fact_id UUID, predicate TEXT, evidence_status TEXT,
  hop_depth INT, path UUID[]
) AS $$
WITH RECURSIVE walk(entity_id, entity_name, entity_type, fact_id, predicate, evidence_status, hop_depth, path) AS (
  SELECT e.id, e.name, e.entity_type,
         NULL::UUID, NULL::TEXT, NULL::TEXT,
         0, ARRAY[e.id]
  FROM borg_entities e
  WHERE e.id = p_entity_id
    AND e.namespace = p_namespace
    AND e.deleted_at IS NULL
  UNION ALL
  SELECT e2.id, e2.name, e2.entity_type,
         f.id, f.predicate, f.evidence_status,
         w.hop_depth + 1, w.path || e2.id
  FROM walk w
  JOIN borg_facts f ON (f.subject_id = w.entity_id OR f.object_id = w.entity_id)
  JOIN borg_entities e2 ON (
    CASE WHEN f.subject_id = w.entity_id THEN f.object_id ELSE f.subject_id END = e2.id
  )
  WHERE w.hop_depth < p_max_hops
    AND f.valid_until IS NULL
    AND f.deleted_at IS NULL
    AND f.namespace = p_namespace
    AND e2.deleted_at IS NULL
    AND NOT e2.id = ANY(w.path)
)
SELECT * FROM walk WHERE hop_depth > 0
ORDER BY hop_depth, entity_name;
$$ LANGUAGE sql STABLE;
