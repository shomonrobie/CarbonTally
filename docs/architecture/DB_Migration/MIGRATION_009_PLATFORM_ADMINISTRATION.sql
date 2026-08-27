-- ============================================
-- MIGRATION 009: PLATFORM ADMINISTRATION
-- Domain 9: Audit Logs, Settings, Flags, Jobs
-- ============================================

-- ============================================
-- 9.1 Audit Logs
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    action_type VARCHAR NOT NULL,
    resource_type VARCHAR,
    resource_id UUID,
    description TEXT,
    ip_address INET,
    user_agent TEXT,
    old_data JSONB,
    new_data JSONB,
    changes JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 9.2 System Settings
-- ============================================

CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    settings_json JSONB,
    max_file_size_mb INTEGER DEFAULT 50,
    allowed_file_types TEXT[] DEFAULT '{".pdf",".csv",".xlsx"}',
    enable_auto_repair BOOLEAN DEFAULT TRUE,
    max_batch_files INTEGER DEFAULT 100,
    max_total_batch_size_mb INTEGER DEFAULT 1000,
    data_retention_days INTEGER DEFAULT 365,
    require_2fa BOOLEAN DEFAULT FALSE,
    session_timeout_minutes INTEGER DEFAULT 60,
    max_login_attempts INTEGER DEFAULT 5,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9.3 Feature Flags
-- ============================================

CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR UNIQUE NOT NULL,
    code VARCHAR UNIQUE NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT FALSE,
    enabled_for_organizations UUID[],
    enabled_for_users UUID[],
    rollout_percentage INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9.4 Background Jobs
-- ============================================

CREATE TABLE IF NOT EXISTS background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR NOT NULL,
    job_data JSONB,
    status VARCHAR DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    priority INTEGER DEFAULT 1,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9.5 API Logs
-- ============================================

CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id),
    organization_id UUID REFERENCES organizations(id),
    endpoint VARCHAR NOT NULL,
    method VARCHAR NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_body JSONB,
    response_body JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9.6 Error Logs
-- ============================================

CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_code VARCHAR,
    error_message TEXT,
    stack_trace TEXT,
    context JSONB,
    severity VARCHAR CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ROLLBACK: MIGRATION 009
-- ============================================

-- DROP TABLE IF EXISTS error_logs;
-- DROP TABLE IF EXISTS api_logs;
-- DROP TABLE IF EXISTS background_jobs;
-- DROP TABLE IF EXISTS feature_flags;
-- DROP TABLE IF EXISTS system_settings;
-- DROP TABLE IF EXISTS audit_logs;