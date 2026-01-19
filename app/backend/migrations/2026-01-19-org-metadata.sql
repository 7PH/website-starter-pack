-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add custom_data JSONB column to organizations table for custom project-specific fields

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS custom_data JSONB DEFAULT '{}' NOT NULL;
