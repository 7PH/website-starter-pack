-- Example Migration: Add index on users.email
-- Date: 2025-12-28
-- Description: Demonstrates common migration patterns

-- Adding an index
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Adding a composite index
-- CREATE INDEX IF NOT EXISTS idx_users_name ON users(first_name, last_name);

-- Altering a column (example - commented out)
-- ALTER TABLE users ALTER COLUMN username TYPE VARCHAR(100);

-- Adding a constraint (example - commented out)
-- ALTER TABLE users ADD CONSTRAINT chk_email_format CHECK (email LIKE '%@%.%');

-- Rollback commands (for reference):
-- DROP INDEX IF EXISTS idx_users_email;
