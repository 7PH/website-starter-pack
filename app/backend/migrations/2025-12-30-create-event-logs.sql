-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
--
-- Event logs table for tracking user and admin actions
-- Note: Indexes are also defined in SQLAlchemy models for fresh installs.
-- This migration ensures indexes exist on databases created before this feature.

CREATE TABLE IF NOT EXISTS event_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes (IF NOT EXISTS ensures idempotency)
CREATE INDEX IF NOT EXISTS ix_event_logs_user_id ON event_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_event_logs_action ON event_logs(action);
CREATE INDEX IF NOT EXISTS ix_event_logs_created_at ON event_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_event_logs_user_created ON event_logs(user_id, created_at DESC);

-- Cleanup: drop actor_id if it exists (removed from schema)
DROP INDEX IF EXISTS ix_event_logs_actor_id;
ALTER TABLE event_logs DROP COLUMN IF EXISTS actor_id;
