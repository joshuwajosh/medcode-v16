-- MedCode AI -- Complete PostgreSQL Schema
-- ========================================
-- Includes: sessions, coded_results, feedback, claims, audit_log (HIPAA)

-- ============================================================
-- Core Application Tables (mirrors SQLite schema)
-- ============================================================

CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
    organization_id TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    clinical_note TEXT,
    note_type TEXT,
    mode TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    processing_time_s REAL,
    confidence_overall REAL,
    needs_human_review INTEGER DEFAULT 0,
    raw_response TEXT
);

CREATE TABLE IF NOT EXISTS coded_results (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) REFERENCES sessions(id) ON DELETE CASCADE,
    organization_id TEXT DEFAULT '',
    code TEXT,
    code_name TEXT,
    vocabulary TEXT,
    code_type TEXT,
    sequence_order INTEGER,
    llm_score INTEGER,
    is_billable INTEGER DEFAULT 0,
    reasoning TEXT,
    confidence_level TEXT
);

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) REFERENCES sessions(id) ON DELETE CASCADE,
    organization_id TEXT DEFAULT '',
    code TEXT,
    action TEXT,
    corrected_code TEXT,
    corrected_by TEXT DEFAULT 'user',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Claims / Billing Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS claims (
    claim_id VARCHAR(64) PRIMARY KEY,
    organization_id TEXT DEFAULT '',
    patient_name TEXT,
    payer_name TEXT,
    provider_npi TEXT,
    total_charges REAL DEFAULT 0.0,
    status VARCHAR(32) DEFAULT 'draft',
    claim_type VARCHAR(32) DEFAULT 'professional',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS claim_status_history (
    id SERIAL PRIMARY KEY,
    claim_id VARCHAR(64) NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    old_status VARCHAR(32),
    new_status VARCHAR(32) NOT NULL,
    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS claim_notes (
    id SERIAL PRIMARY KEY,
    claim_id VARCHAR(64) NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    note_type VARCHAR(32) DEFAULT 'general',
    content TEXT,
    created_by VARCHAR(64) DEFAULT 'system',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- HIPAA Audit Log (§164.312(b))
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR(64) NOT NULL,
    actor TEXT,
    resource_type VARCHAR(64),
    resource_id VARCHAR(64),
    action VARCHAR(32) NOT NULL,
    outcome VARCHAR(16) DEFAULT 'success',
    detail JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(64)
);

-- ============================================================
-- Webhook Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS webhooks (
    id VARCHAR(64) PRIMARY KEY,
    organization_id TEXT NOT NULL,
    url TEXT NOT NULL,
    events TEXT NOT NULL,
    secret TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id VARCHAR(64) PRIMARY KEY,
    webhook_id VARCHAR(64) NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    status VARCHAR(16) DEFAULT 'pending',
    response_code INTEGER,
    delivered_at TIMESTAMPTZ
);

-- ============================================================
-- Tenant Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(64) PRIMARY KEY,
    name TEXT NOT NULL,
    plan VARCHAR(32) DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    active INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Batch Processing Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS batches (
    batch_id VARCHAR(64) PRIMARY KEY,
    organization_id TEXT DEFAULT '',
    status VARCHAR(32) DEFAULT 'pending',
    total_claims INTEGER DEFAULT 0,
    processed INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    progress_pct REAL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error TEXT,
    result_json TEXT
);

CREATE TABLE IF NOT EXISTS batch_claims (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    claim_index INTEGER NOT NULL,
    claim_id VARCHAR(64),
    status VARCHAR(32) DEFAULT 'pending',
    result_json TEXT
);

-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_results_session ON coded_results(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id);

CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_payer ON claims(payer_name);
CREATE INDEX IF NOT EXISTS idx_claims_updated ON claims(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_history_claim ON claim_status_history(claim_id);
CREATE INDEX IF NOT EXISTS idx_notes_claim ON claim_notes(claim_id);

CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_webhooks_org ON webhooks(organization_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_webhook ON webhook_deliveries(webhook_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON webhook_deliveries(status);
CREATE INDEX IF NOT EXISTS idx_tenants_name ON tenants(name);
CREATE INDEX IF NOT EXISTS idx_tenants_plan ON tenants(plan);

CREATE INDEX IF NOT EXISTS idx_sessions_org ON sessions(organization_id);
CREATE INDEX IF NOT EXISTS idx_claims_org ON claims(organization_id);

CREATE INDEX IF NOT EXISTS idx_batches_org ON batches(organization_id);
CREATE INDEX IF NOT EXISTS idx_batches_status ON batches(status);
CREATE INDEX IF NOT EXISTS idx_batches_created ON batches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_batch_claims_batch ON batch_claims(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_claims_status ON batch_claims(status);

CREATE INDEX IF NOT EXISTS idx_results_code ON coded_results(code);
CREATE INDEX IF NOT EXISTS idx_results_vocabulary ON coded_results(vocabulary);
CREATE INDEX IF NOT EXISTS idx_feedback_code ON feedback(code);
CREATE INDEX IF NOT EXISTS idx_feedback_action ON feedback(action);
