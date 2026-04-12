#!/usr/bin/env bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
#
# Wait for services to be ready by polling a health check URL.
# Usage: bash scripts/_core/wait-for-services.sh [--url URL] [--timeout SECONDS]

set -euo pipefail

URL="http://localhost:13001/api/v1/healthcheck"
TIMEOUT=120

while [[ $# -gt 0 ]]; do
    case $1 in
        --url) URL="$2"; shift 2 ;;
        --timeout) TIMEOUT="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

echo "Waiting for $URL (timeout: ${TIMEOUT}s)..."

start=$(date +%s)
while true; do
    elapsed=$(( $(date +%s) - start ))
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
        echo "Timed out after ${TIMEOUT}s waiting for $URL"
        exit 1
    fi

    if curl -sf "$URL" > /dev/null 2>&1; then
        echo "Services ready after ${elapsed}s"
        exit 0
    fi

    sleep 2
done
