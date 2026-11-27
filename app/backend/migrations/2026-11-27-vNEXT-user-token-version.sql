-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
--
-- Every JWT carries the user's token_version; bumping it signs the user out everywhere.
-- Rollback: ALTER TABLE users DROP COLUMN IF EXISTS token_version;

ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;
