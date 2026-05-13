#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
#
# Upsert a known roster of password-auth users via /internal/seed-users so
# preview stacks (and local dev) come up with predictable logins. Idempotent:
# re-running with the same payload only updates flags.
#
# Apps override the default roster by setting PREVIEW_SEED_USERS in
# .env.preview.app to a JSON array (see the commented example there).
#
# Two transport modes:
#   - SEED_NETWORK unset (local dev): direct curl to ${PUBLIC_URL}.
#   - SEED_NETWORK=<docker-network> (CI preview): curl runs inside that
#     network with `Host: ${SEED_HOST_HEADER}` so per-PR Traefik routes
#     correctly. The host runner can't resolve container names directly,
#     and the public hostname may not resolve from the runner either.
#
# Env (read from .env in local mode):
#   PUBLIC_URL          base URL of the running backend (local mode)
#   INTERNAL_API_KEY    shared secret for /internal/* routes
#   PREVIEW_SEED_USERS  optional JSON array overriding the default roster
#   SEED_NETWORK        opt-in: docker network for CI preview transport
#   SEED_HOST_HEADER    required when SEED_NETWORK is set: virtual host
#   SEED_TARGET         required when SEED_NETWORK is set: container target,
#                       e.g. "${COMPOSE_PROJECT_NAME}-traefik"

set -euo pipefail

if [ -z "${INTERNAL_API_KEY:-}" ]; then
  echo "Error: INTERNAL_API_KEY is empty. Set it in .env (see .env.template) and restart the backend." >&2
  exit 1
fi

DEFAULT_ROSTER='[
  {"email": "admin@preview.app",   "password": "preview-admin",   "is_admin": true,  "first_name": "Preview", "last_name": "Admin"},
  {"email": "user@preview.app",    "password": "preview-user",                       "first_name": "Preview", "last_name": "User"},
  {"email": "premium@preview.app", "password": "preview-premium", "is_premium": true,"first_name": "Preview", "last_name": "Premium"}
]'

ROSTER="${PREVIEW_SEED_USERS:-$DEFAULT_ROSTER}"

# Wrap roster into the endpoint's request schema; fail clearly on bad JSON.
BODY=$(printf '%s' "$ROSTER" | python3 -c '
import json, sys
try:
    roster = json.load(sys.stdin)
except json.JSONDecodeError as e:
    raise SystemExit(f"PREVIEW_SEED_USERS is not valid JSON: {e}")
if not isinstance(roster, list):
    raise SystemExit("PREVIEW_SEED_USERS must be a JSON array of user specs")
print(json.dumps({"users": roster}))
')

if [ -n "${SEED_NETWORK:-}" ]; then
  : "${SEED_HOST_HEADER:?SEED_HOST_HEADER must be set when SEED_NETWORK is set}"
  : "${SEED_TARGET:?SEED_TARGET must be set when SEED_NETWORK is set}"
  URL="http://${SEED_TARGET}/api/v1/internal/seed-users"
  RESPONSE=$(printf '%s' "$BODY" | docker run --rm -i \
    --network "$SEED_NETWORK" \
    curlimages/curl:latest \
    -fsS -X POST \
    -H "Content-Type: application/json" \
    -H "X-Internal-API-Key: ${INTERNAL_API_KEY}" \
    -H "Host: ${SEED_HOST_HEADER}" \
    --data-binary @- \
    "$URL")
else
  if [ -z "${PUBLIC_URL:-}" ]; then
    echo "Error: PUBLIC_URL is not set. Run via 'npm run seed-preview-users' so .env is loaded." >&2
    exit 1
  fi
  URL="${PUBLIC_URL}/api/v1/internal/seed-users"
  RESPONSE=$(curl -fsS -X POST \
    -H "Content-Type: application/json" \
    -H "X-Internal-API-Key: ${INTERNAL_API_KEY}" \
    --data-binary "$BODY" \
    "$URL")
fi

printf '%s\n---\n%s' "$BODY" "$RESPONSE" | python3 -c '
import json, sys
raw = sys.stdin.read()
sent_raw, _, resp_raw = raw.partition("\n---\n")
sent = {u["email"].lower(): u for u in json.loads(sent_raw).get("users", [])}
results = json.loads(resp_raw).get("results", [])
for r in results:
    spec = sent.get(r["email"].lower(), {})
    print("  %8s  %s / %s" % (r["status"], r["email"], spec.get("password", "?")))
print("Seeded %d users." % len(results))
'
