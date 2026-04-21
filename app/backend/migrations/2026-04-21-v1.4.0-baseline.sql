-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Baseline migration for starterpack v1.4.0.
-- Consolidation of every v1.0.0 → v1.4.0 migration, concatenated in date order.
-- Idempotent: safe to re-run thanks to IF NOT EXISTS / IF EXISTS guards.


-- ─── Originally: 2026-01-06-soft-delete-users.sql ───
-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add soft delete support for users
-- When a user is deleted, their data is anonymized and deleted_at is set

-- Add deleted_at column
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Create index for filtering active users efficiently
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);

-- ─── Originally: 2026-01-09-organizations.sql ───
-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

-- Add organizations feature
-- Organizations allow grouping users with shared premium subscriptions

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,

    -- Basic info
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Billing info
    phone VARCHAR(50),
    tax_number VARCHAR(100),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(2),

    -- Stripe
    stripe_id VARCHAR(255) UNIQUE,
    stripe_premium BOOLEAN DEFAULT FALSE,
    stripe_quota INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ DEFAULT NULL
);

-- Create indexes for organizations
CREATE INDEX IF NOT EXISTS idx_organizations_deleted_at ON organizations(deleted_at);
CREATE INDEX IF NOT EXISTS idx_organizations_stripe_id ON organizations(stripe_id);

-- Create user_organizations mapping table
CREATE TABLE IF NOT EXISTS user_organizations (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, organization_id)
);

-- Create indexes for user_organizations lookups
CREATE INDEX IF NOT EXISTS idx_user_organizations_org_id ON user_organizations(organization_id);
CREATE INDEX IF NOT EXISTS idx_user_organizations_user_id ON user_organizations(user_id);

-- Premium source tracking
-- Track personal subscription explicitly on users
ALTER TABLE users ADD COLUMN IF NOT EXISTS has_personal_subscription BOOLEAN DEFAULT FALSE;

-- Track premium seat on org membership
ALTER TABLE user_organizations ADD COLUMN IF NOT EXISTS has_premium_seat BOOLEAN DEFAULT FALSE;

-- Backfill: users with is_premium=true and no org membership have personal subscription
UPDATE users SET has_personal_subscription = TRUE
WHERE is_premium = TRUE
AND id NOT IN (SELECT user_id FROM user_organizations);

-- Backfill: users with is_premium=true and org membership have org seat
-- (Assumes premium came from org if user is in a premium org)
UPDATE user_organizations SET has_premium_seat = TRUE
WHERE user_id IN (SELECT id FROM users WHERE is_premium = TRUE)
AND organization_id IN (SELECT id FROM organizations WHERE stripe_premium = TRUE);

-- ─── Originally: 2026-01-14-oauth-provider.sql ───
-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add OAuth provider tracking columns to users table
-- This allows tracking which OAuth provider was used to create the account
-- and the provider's unique user ID for account linking.

ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_id VARCHAR;

-- Rollback:
-- ALTER TABLE users DROP COLUMN IF EXISTS oauth_provider;
-- ALTER TABLE users DROP COLUMN IF EXISTS oauth_id;

-- ─── Originally: 2026-01-16-conversations.sql ───
-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add messaging/conversation system
-- Supports support tickets (user-to-admin) and future direct messages (user-to-user)

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,

    -- Conversation metadata
    type VARCHAR(50) NOT NULL DEFAULT 'support',
    subject VARCHAR(255),

    -- Creator (for support: the user who opened the ticket)
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Status
    is_closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(type);
CREATE INDEX IF NOT EXISTS idx_conversations_created_by_id ON conversations(created_by_id);
CREATE INDEX IF NOT EXISTS idx_conversations_is_closed ON conversations(is_closed);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Message content
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,

    -- Admin flag for support conversations
    is_admin_response BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Create conversation participants table (for future direct messages and read tracking)
CREATE TABLE IF NOT EXISTS conversation_participants (
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Read tracking
    last_read_at TIMESTAMPTZ,

    -- Timestamps
    joined_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (conversation_id, user_id)
);

-- Create indexes for participants
CREATE INDEX IF NOT EXISTS idx_conversation_participants_user_id ON conversation_participants(user_id);

-- ─── Originally: 2026-01-19-org-metadata.sql ───
-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add custom_data JSONB column to organizations table for custom project-specific fields

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS custom_data JSONB DEFAULT '{}' NOT NULL;

-- ─── Originally: 2026-04-16-conversation-subtype.sql ───
-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add optional subtype column to conversations

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS subtype VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_conversations_subtype ON conversations(subtype);

-- ─── Originally: 2026-04-20-org-invitations.sql ───
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

-- ─── Originally: 2026-04-21-organization-billing.sql ───
-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

-- Admin-managed billing for organizations.
-- Lets an admin assign a plan to an org manually (bank-transfer customers) and
-- drive a monthly balance decrement without creating a real Stripe subscription.
-- The running balance itself lives in Stripe (customer.balance); these columns
-- just track which plan the admin assigned and when the next cycle fires.

ALTER TABLE organizations
    ADD COLUMN IF NOT EXISTS billing_price_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS billing_cycle_started_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS billing_cycle_end TIMESTAMPTZ;

-- Partial index so the daily task scans only orgs with an assigned plan.
CREATE INDEX IF NOT EXISTS idx_organizations_billing_cycle_end
    ON organizations(billing_cycle_end)
    WHERE billing_price_id IS NOT NULL;

-- ─── Originally: 2026-04-21-user-metadata.sql ───
-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
-- Add custom_data JSONB column to users table for custom project-specific fields

ALTER TABLE users ADD COLUMN IF NOT EXISTS custom_data JSONB DEFAULT '{}' NOT NULL;
