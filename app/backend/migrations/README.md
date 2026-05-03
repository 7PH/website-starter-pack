# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

# Database Migrations

This folder contains manual SQL migration files for schema changes that SQLAlchemy can't auto-generate.

## When to Use

SQLAlchemy's `Base.metadata.create_all()` handles initial table creation. Use migrations for:

- Adding indexes
- Altering column types or constraints
- Renaming columns/tables
- Data migrations
- Adding database-level constraints

## Naming Convention

New migrations during dev use the `vNEXT` placeholder:

```
YYYY-MM-DD-vNEXT-description.sql
```

Example: `2026-04-21-vNEXT-add-users-email-index.sql`

At release time, the `release-starterpack` skill rewrites `vNEXT` to the target
version, producing the final name:

```
YYYY-MM-DD-vX.Y.Z-description.sql
```

Example: `2026-04-21-v2.0.0-add-users-email-index.sql`

### Baseline

`2026-04-21-v1.4.0-baseline.sql` is the consolidation of every v1.0.0 → v1.4.0
migration. Fresh installs run it once. Existing sub-apps that have already
applied the individual pre-v2.0.0 migrations can treat it as a no-op — it uses
`IF NOT EXISTS` guards throughout.

## How to Run

### Via Adminer (Development)

1. Open Adminer at `http://${ADMINER_SUBDOMAIN}.${PUBLIC_WEBSITE_HOST}` (default `http://adminer.localhost`)
2. Connect to the database
3. Go to "SQL command"
4. Paste the migration SQL and execute

### Via psql (CLI)

```bash
docker exec -i <container-name>-db psql -U postgres -d app < migrations/2025-12-28-example.sql
```

### Via Docker Compose

```bash
docker compose exec db psql -U postgres -d app -f /path/to/migration.sql
```

## Best Practices

1. **Make migrations idempotent** - Always use `IF NOT EXISTS` / `IF EXISTS` so migrations can be safely re-run without errors:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_name ON table(column);
   DROP INDEX IF EXISTS idx_name;
   ALTER TABLE table ADD COLUMN IF NOT EXISTS column_name TYPE;
   ```
2. **One migration per file** - Keep changes atomic
3. **Test locally first** - Run on development before production
4. **Include rollback comments** - Document how to undo changes
5. **Coordinate with model changes** - Update SQLAlchemy models to match
