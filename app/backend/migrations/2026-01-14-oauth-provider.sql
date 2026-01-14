-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add OAuth provider tracking columns to users table
-- This allows tracking which OAuth provider was used to create the account
-- and the provider's unique user ID for account linking.

ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_id VARCHAR;

-- Rollback:
-- ALTER TABLE users DROP COLUMN IF EXISTS oauth_provider;
-- ALTER TABLE users DROP COLUMN IF EXISTS oauth_id;
