-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

-- Add email invitation flow for organizations.
-- Owners can invite members via email; recipients accept or decline via a token link.

CREATE TABLE IF NOT EXISTS organization_invitations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    is_admin_invite BOOLEAN NOT NULL DEFAULT FALSE,
    token VARCHAR(64) NOT NULL UNIQUE,
    invited_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    declined_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_org_invitations_email_expires
    ON organization_invitations(email, expires_at);

CREATE INDEX IF NOT EXISTS idx_org_invitations_org_id
    ON organization_invitations(organization_id);

CREATE INDEX IF NOT EXISTS idx_org_invitations_token
    ON organization_invitations(token);
