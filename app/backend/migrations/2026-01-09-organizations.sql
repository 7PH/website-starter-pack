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
