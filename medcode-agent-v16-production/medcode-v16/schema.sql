-- MedCode AI -- Complete PostgreSQL Schema
-- ========================================
-- Includes: sessions, coded_results, feedback, claims, audit_log (HIPAA)

-- ============================================================
-- Core Application Tables (mirrors SQLite schema)
-- ============================================================

CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
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
