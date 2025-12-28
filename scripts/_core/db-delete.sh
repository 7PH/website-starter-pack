#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

# Confirm deletion
echo "WARNING: You are about to delete all data in the database '$APP_DB_NAME'."
read -p "Are you sure you want to proceed? This will delete all data permanently. (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Operation canceled."
  exit 0
fi

# Check if the database container is running
DB_CONTAINER=$(docker container list --filter "name=db" --format "{{.ID}}")

if [ -n "$DB_CONTAINER" ]; then
  echo "Error: Database container 'db' is still running. Please stop it first."
  exit 1
fi

# Delete the database data directory
DATA_DIR="services/db/data"
if [ -d "$DATA_DIR" ]; then
  echo "Emptying database data directory '$DATA_DIR'..."
  sudo rm -rf "$DATA_DIR/*"
  if [ $? -eq 0 ]; then
    echo "Database data directory '$DATA_DIR' successfully emptied."
  else
    echo "Failed to empty the database data directory '$DATA_DIR'."
    exit 1
  fi
else
  echo "Database data directory '$DATA_DIR' does not exist."
fi
