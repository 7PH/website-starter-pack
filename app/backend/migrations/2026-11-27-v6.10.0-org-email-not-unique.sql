-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
--
-- Several organizations may share an email, eg two orgs created by the same user.
-- Rollback: ALTER TABLE organizations ADD CONSTRAINT organizations_email_key UNIQUE (email);

ALTER TABLE organizations DROP CONSTRAINT IF EXISTS organizations_email_key;
