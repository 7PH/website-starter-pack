-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
--
-- Add the public username handle (USERNAMES_ENABLED).
--
-- Locking: ADD COLUMN is metadata-only in PG11+, but CREATE UNIQUE INDEX takes a
-- SHARE lock and blocks writes to users while it builds. That is brief on a
-- small table but not on a large one, and it happens whether or not the flag is
-- on. For a big users table, run the index separately with CONCURRENTLY
-- (outside a transaction) instead of the statement below:
--
--   CREATE UNIQUE INDEX CONCURRENTLY idx_users_username_lower
--       ON users (lower(username)) WHERE username IS NOT NULL;
--
-- Apps that already have their own `username` column: ADD COLUMN skips, and the
-- index below then builds against existing rows. If case-variant handles were
-- ever allowed it fails and aborts the migration. Check first:
--
--   SELECT lower(username), count(*) FROM users
--   WHERE username IS NOT NULL GROUP BY 1 HAVING count(*) > 1;

ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(32);

-- Case-insensitive: a plain UNIQUE would let "Bob" and "bob" coexist.
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_lower
    ON users (lower(username)) WHERE username IS NOT NULL;
