#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
#
# Mint a JWT for an existing user via the backend's /internal/mint-token route
# and print a JS snippet that injects it into a Playwright browser session via
# localStorage. Used by Claude Code for auth-gated UI checks without going
# through the login form.
#
# Requires INTERNAL_API_KEY in .env, and INTERNAL_API_ENABLED=true in prod
# (the route is unregistered
# otherwise — see app/backend/src/controllers/internal.py).
#
# Usage:
#   bash scripts/_core/dev-mint-token.sh                  # JS snippet for first admin
#   bash scripts/_core/dev-mint-token.sh <email>          # JS snippet for that user
#   bash scripts/_core/dev-mint-token.sh <email> --json   # raw token JSON
#   bash scripts/_core/dev-mint-token.sh <email> --jwt    # bare access_token (for curl)
#   bash scripts/_core/dev-mint-token.sh '' --jwt         # default user, jwt-only mode
#
# Env (read from .env via the npm wrapper):
#   PUBLIC_URL          base URL of the running backend
#   INTERNAL_API_KEY    shared secret for /internal/* routes

set -euo pipefail

# Allow either `<email> [mode]` or just `[mode]` (when no email given).
if [ $# -ge 1 ] && [[ "$1" == --* ]]; then
  EMAIL=""
  MODE="$1"
else
  EMAIL="${1:-}"
  MODE="${2:---js}"
fi

if [ -z "${PUBLIC_URL:-}" ]; then
  echo "Error: PUBLIC_URL is not set. Run via 'npm run dev-mint-token -- <email>' so .env is loaded." >&2
  exit 1
fi

if [ -z "${INTERNAL_API_KEY:-}" ]; then
  echo "Error: INTERNAL_API_KEY is empty. Set it in .env (see .env.template) and restart the backend." >&2
  exit 1
fi

if [ -n "$EMAIL" ]; then
  BODY=$(python3 -c 'import json,sys; print(json.dumps({"email": sys.argv[1]}))' "$EMAIL")
else
  BODY='{}'
fi

RESPONSE=$(curl -fsS -X POST \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: ${INTERNAL_API_KEY}" \
  --data-binary "$BODY" \
  "${PUBLIC_URL}/api/v1/internal/mint-token")

case "$MODE" in
  --json)
    printf '%s\n' "$RESPONSE"
    ;;
  --jwt)
    printf '%s\n' "$RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
    ;;
  --js|*)
    ESCAPED=$(printf '%s' "$RESPONSE" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
    printf "() => { localStorage.setItem('user-token', %s); return 'ok'; }\n" "$ESCAPED"
    ;;
esac
