#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

if [ -z "$APP_DB_NAME" ] || [ -z "$APP_DB_USER" ] || [ -z "$APP_DB_PASSWORD" ]; then
  echo "Database configuration is missing in .env file"
  exit 1
fi

if [ -z "$1" ]; then
  echo "Usage: $0 <path_to_backup_file>"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file '$BACKUP_FILE' not found"
  exit 1
fi

# Use project name to find the exact db container (not umami-db)
DB_CONTAINER_NAME="${COMPOSE_PROJECT_NAME:-starterpack}-db"
DB_CONTAINER=$(docker container list --filter "name=^${DB_CONTAINER_NAME}$" --format "{{.ID}}" 2>/dev/null)
# Fallback: try exact name match with docker inspect
if [ -z "$DB_CONTAINER" ]; then
  DB_CONTAINER=$(docker inspect --format '{{.Id}}' "$DB_CONTAINER_NAME" 2>/dev/null)
fi

if [ -z "$DB_CONTAINER" ]; then
  echo "Database container '$DB_CONTAINER_NAME' is not running"
  exit 1
fi

echo "Restoring database '$APP_DB_NAME' from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" sh -c "PGPASSWORD=$APP_DB_PASSWORD psql -U $APP_DB_USER -d $APP_DB_NAME"

if [ $? -eq 0 ]; then
  echo "Database successfully restored from $BACKUP_FILE"
else
  echo "Database restore failed"
  exit 1
fi
