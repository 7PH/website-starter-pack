#!/bin/bash

export $(grep -v '^#' .env | xargs)

if [ -z "$APP_DB_NAME" ] || [ -z "$APP_DB_USER" ] || [ -z "$APP_DB_PASSWORD" ]; then
  echo "Database configuration is missing in .env file"
  exit 1
fi

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

DATE=$(date +%Y-%m-%d_%H-%M-%S)
DUMP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

DB_CONTAINER=$(docker container list --filter "name=db" --format "{{.ID}}")

if [ -z "$DB_CONTAINER" ]; then
  echo "Database container 'db' is not running"
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
