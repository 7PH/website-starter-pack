#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

# Get backend container using project name
BACKEND_CONTAINER_NAME="${COMPOSE_PROJECT_NAME:-starterpack}-backend"
BACKEND_CONTAINER=$(docker container list --filter "name=^${BACKEND_CONTAINER_NAME}$" --format "{{.ID}}" 2>/dev/null)
# Fallback: try exact name match with docker inspect
if [ -z "$BACKEND_CONTAINER" ]; then
  BACKEND_CONTAINER=$(docker inspect --format '{{.Id}}' "$BACKEND_CONTAINER_NAME" 2>/dev/null)
fi

# Exit if backend container is not running
if [ -z "$BACKEND_CONTAINER" ]; then
  echo "Error: Backend container '$BACKEND_CONTAINER_NAME' is not running. Please start the container first."
  exit 1
fi

# Convert models and write to models.json
docker exec $BACKEND_CONTAINER python -m src.convert-models > app/frontend/types/models.json

# Convert JSON Schema to TypeScript
./node_modules/.bin/json2ts \
  --additionalProperties=false \
  app/frontend/types/models.json > app/frontend/types/models.ts

# Fix the file for global declaration
echo -e "export {};\ndeclare global {\n$(cat app/frontend/types/models.ts)\n}" > app/frontend/types/models.ts
