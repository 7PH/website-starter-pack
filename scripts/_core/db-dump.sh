#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

if [ -z "$APP_DB_NAME" ] || [ -z "$APP_DB_USER" ] || [ -z "$APP_DB_PASSWORD" ]; then
  echo "Database configuration is missing in .env file"
  exit 1
fi

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

DATE=$(date +%Y-%m-%d_%H-%M-%S)
DUMP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

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

echo "Dumping and compressing database '$APP_DB_NAME' content from container 'db'..."
docker exec -it "$DB_CONTAINER" sh -c "PGPASSWORD=$APP_DB_PASSWORD pg_dump -U $APP_DB_USER $APP_DB_NAME" | gzip > "$DUMP_FILE.gz"

if [ $? -eq 0 ]; then
  echo "Database dump successfully saved to $DUMP_FILE.gz"
else
  echo "Database dump failed"
  exit 1
fi
