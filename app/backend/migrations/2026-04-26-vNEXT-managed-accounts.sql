-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
--
-- Managed accounts: email-less users grouped under an owner, signing in by code.
--
-- New on users:
--   auth_method                — 'password' | 'oauth' | 'access_code' | 'deleted', enforced by CHECK
--   display_name               — preferred label, first in the display ladder
--   managed_account_group_id   — FK to managed_account_groups(id), set for managed accounts
--
-- New tables:
--   managed_account_groups     — owner_id + name + share_token (public picker URL)
--   access_codes               — code → user_id mapping consumed by /auth/code
--
-- Apps that don't need this concept can ignore the columns/tables.
--
-- ROLLBACK: irreversible once any user has auth_method='access_code' or 'deleted'.

-- ─── users column changes ───
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;
ALTER TABLE users ALTER COLUMN first_name DROP NOT NULL;
ALTER TABLE users ALTER COLUMN last_name DROP NOT NULL;
ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS auth_method VARCHAR(32) NOT NULL DEFAULT 'password';

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Backfill: any row with oauth_provider set is oauth (account-linking can also
-- leave hashed_password set, so don't key on that).
UPDATE users SET auth_method = 'oauth' WHERE oauth_provider IS NOT NULL;

-- CHECK constraint: enforce auth-path integrity at the DB level.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_auth_integrity') THEN
        ALTER TABLE users ADD CONSTRAINT users_auth_integrity CHECK (
            (auth_method = 'password'    AND email IS NOT NULL AND hashed_password IS NOT NULL AND oauth_provider IS NULL)
            OR (auth_method = 'oauth'    AND email IS NOT NULL AND oauth_provider IS NOT NULL)
            OR (auth_method = 'access_code')
            OR (auth_method = 'deleted')
        );
    END IF;
END$$;

-- ─── managed_account_groups table ───
CREATE TABLE IF NOT EXISTS managed_account_groups (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    share_token VARCHAR(32) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_managed_account_groups_owner_id ON managed_account_groups(owner_id);
CREATE INDEX IF NOT EXISTS idx_managed_account_groups_share_token ON managed_account_groups(share_token);

-- Now that the target table exists, add the FK column on users.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS managed_account_group_id INTEGER
        REFERENCES managed_account_groups(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_users_managed_account_group_id
    ON users(managed_account_group_id);

-- ─── access_codes table ───
-- PK is composite (user_id, code) so the same code string can be issued to
-- managed accounts under unrelated managers. Sign-in always passes both halves.
CREATE TABLE IF NOT EXISTS access_codes (
    code VARCHAR(64) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    revoked_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, code)
);

CREATE INDEX IF NOT EXISTS idx_access_codes_user ON access_codes(user_id);

-- If an earlier draft of this migration created `code` as the sole PK, swap
-- to the composite. Idempotent: no-op when already correct.
DO $$
DECLARE
    pk_columns TEXT;
BEGIN
    SELECT string_agg(a.attname, ',' ORDER BY array_position(c.conkey, a.attnum))
    INTO pk_columns
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
    WHERE c.conrelid = 'access_codes'::regclass AND c.contype = 'p';

    IF pk_columns = 'code' THEN
        ALTER TABLE access_codes DROP CONSTRAINT access_codes_pkey;
        ALTER TABLE access_codes ADD CONSTRAINT access_codes_pkey PRIMARY KEY (user_id, code);
    END IF;
END$$;
