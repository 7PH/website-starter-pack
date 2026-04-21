-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add custom_data JSONB column to users table for custom project-specific fields

ALTER TABLE users ADD COLUMN IF NOT EXISTS custom_data JSONB DEFAULT '{}' NOT NULL;
