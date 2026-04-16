#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
# Run a SQL migration file against the database.
# Usage: npm run db-migrate -- <migration-file>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

# Require a migration file argument
if [ -z "$1" ]; then
  print_error "Usage: npm run db-migrate -- <migration-file>"
  echo "  Example: npm run db-migrate -- app/backend/migrations/2026-04-16-conversation-subtype.sql"
  exit 1
fi

MIGRATION_FILE="$1"

if [ ! -f "$MIGRATION_FILE" ]; then
  print_error "File not found: $MIGRATION_FILE"
  exit 1
fi

# Ensure required environment variables are present
if [ -z "$APP_DB_NAME" ] || [ -z "$APP_DB_USER" ] || [ -z "$APP_DB_PASSWORD" ]; then
  print_error "Database configuration is missing in the environment variables."
  exit 1
fi

# Find the database container
DB_CONTAINER_NAME="${COMPOSE_PROJECT_NAME:-starterpack}-db"
DB_CONTAINER=$(docker container list --filter "name=^${DB_CONTAINER_NAME}$" --format "{{.ID}}" 2>/dev/null)
if [ -z "$DB_CONTAINER" ]; then
  DB_CONTAINER=$(docker inspect --format '{{.Id}}' "$DB_CONTAINER_NAME" 2>/dev/null)
fi

if [ -z "$DB_CONTAINER" ]; then
  print_error "Database container '$DB_CONTAINER_NAME' is not running. Please start the container first."
  exit 1
fi

print_info "Running migration: $MIGRATION_FILE"
docker exec -i "$DB_CONTAINER" sh -c "PGPASSWORD=$APP_DB_PASSWORD psql -U $APP_DB_USER -d $APP_DB_NAME" < "$MIGRATION_FILE"
print_success "Migration completed: $MIGRATION_FILE"
