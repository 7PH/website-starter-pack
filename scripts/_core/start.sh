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

docker compose --profile prod up -d --build
bash "$SCRIPT_DIR/wait-for-services.sh" --url "$HEALTHCHECK_URL" --timeout 60
bash "$SCRIPT_DIR/print-dev-banner.sh" --mode prod
