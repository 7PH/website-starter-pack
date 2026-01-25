-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add soft delete support for users
-- When a user is deleted, their data is anonymized and deleted_at is set

-- Add deleted_at column
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Create index for filtering active users efficiently
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);
