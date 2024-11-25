#!/bin/bash

export $(grep -v '^#' .env | xargs)

# Ensure required variables are set
if [ -z "$APP_DB_NAME" ] || [ -z "$APP_DB_USER" ] || [ -z "$APP_DB_PASSWORD" ]; then
  echo "Database configuration is missing in .env file"
  exit 1
fi

# Set the output file for the database dump
DUMP_FILE="./services/db/initdb.sql"

# Get the database container ID by its name
DB_CONTAINER=$(docker container list --filter "name=db" --format "{{.ID}}")

# Exit if the database container is not running
if [ -z "$DB_CONTAINER" ]; then
  echo "Database container 'db' is not running"
  exit 1
fi

# Dump the database to the specified file
echo "Dumping database '$APP_DB_NAME' content from container 'db' to $DUMP_FILE..."
docker exec -it "$DB_CONTAINER" sh -c "PGPASSWORD=$APP_DB_PASSWORD pg_dump -U $APP_DB_USER $APP_DB_NAME" > "$DUMP_FILE"

# Check if the dump was successful
if [ $? -eq 0 ]; then
  echo "Database dump successfully saved to $DUMP_FILE"
else
  echo "Database dump failed"
  exit 1
fi
