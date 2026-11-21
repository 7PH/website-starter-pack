#!/usr/bin/env bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
#
# Starts the prod stack, waits for the backend to be reachable,
# then prints a summary banner.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

HEALTHCHECK_URL="${PUBLIC_URL:-http://localhost}/api/v1/healthcheck"

# Built first: some Compose versions decide what to recreate before `up --build` finishes building, and keep the old containers
docker compose --profile prod build
docker compose --profile prod up -d
# The backend code is bind-mounted, not baked into its image, so a code-only change needs a restart
docker compose --profile prod restart backend-prod

# A container still on an older image keeps serving the previous build without any error: say it loudly
stale=0
for cid in $(docker compose --profile prod ps -q); do
    read -r name image running < <(docker inspect -f '{{.Name}} {{.Config.Image}} {{.Image}}' "$cid")
    if [ "$(docker image inspect -f '{{.Id}}' "$image")" != "$running" ]; then
        echo "ERROR: ${name#/} still runs an older image than $image" >&2
        stale=1
    fi
done
if [ "$stale" -ne 0 ]; then
    echo "Run 'docker compose --profile prod up -d --force-recreate' to swap them" >&2
    exit 1
fi
bash "$SCRIPT_DIR/wait-for-services.sh" --url "$HEALTHCHECK_URL" --timeout 60
bash "$SCRIPT_DIR/print-dev-banner.sh" --mode prod
