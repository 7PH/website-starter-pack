#!/bin/bash

# Get backend container
BACKEND_CONTAINER=$(docker container list --filter "name=backend" --format "{{.ID}}")

# Exit if backend container is not running
if [ -z $BACKEND_CONTAINER ]; then
  echo "Backend container is not running"
  exit 1
fi

# Convert models and write to models.json
docker exec -it $BACKEND_CONTAINER python -m src.convert-models > app/frontend/types/models.json

# Convert JSON Schema to TypeScript
./node_modules/.bin/json2ts \
  --additionalProperties=false \
  app/frontend/types/models.json > app/frontend/types/models.ts

# Fix the file for global declaration
echo -e "export { };\ndeclare global {\n$(cat app/frontend/types/models.ts)\n}" > app/frontend/types/models.ts
