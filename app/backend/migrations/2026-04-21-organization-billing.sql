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
