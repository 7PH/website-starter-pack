-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add optional subtype column to conversations

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS subtype VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_conversations_subtype ON conversations(subtype);
