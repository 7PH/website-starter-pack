#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

# Ensure required environment variables are present
if [ -z "$APP_DB_NAME" ] || [ -z "$APP_DB_USER" ] || [ -z "$APP_DB_PASSWORD" ]; then
  echo "Database configuration is missing in the environment variables."
  exit 1
fi

# Check if the database container is running
# Use project name to find the exact db container (not umami-db)
DB_CONTAINER_NAME="${COMPOSE_PROJECT_NAME:-starterpack}-db"
DB_CONTAINER=$(docker container list --filter "name=^${DB_CONTAINER_NAME}$" --format "{{.ID}}" 2>/dev/null)
# Fallback: try exact name match with docker inspect
if [ -z "$DB_CONTAINER" ]; then
  DB_CONTAINER=$(docker inspect --format '{{.Id}}' "$DB_CONTAINER_NAME" 2>/dev/null)
fi

if [ -z "$DB_CONTAINER" ]; then
  echo "Error: Database container 'db' is not running. Please start the container first."
  exit 1
fi

# Connect to the PostgreSQL database
echo "Connecting to the database '$APP_DB_NAME'..."
docker exec -it "$DB_CONTAINER" sh -c "PGPASSWORD=$APP_DB_PASSWORD psql -U $APP_DB_USER -d $APP_DB_NAME"
