#!/usr/bin/env bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
#
# Prints a summary banner of URLs and feature flags for the running stack.
# Usage: bash scripts/_core/print-dev-banner.sh [--mode dev|prod]

set -eu

MODE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --mode) MODE="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

if [ -z "$MODE" ]; then
    if docker compose ps --services --filter status=running 2>/dev/null | grep -qx "traefik-dev"; then
        MODE="dev"
    elif docker compose ps --services --filter status=running 2>/dev/null | grep -qx "traefik-prod"; then
        MODE="prod"
    else
        MODE="dev"
    fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=utils.sh
. "$SCRIPT_DIR/utils.sh"

if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

PUBLIC_WEBSITE_HOST="${PUBLIC_WEBSITE_HOST:-localhost}"
PUBLIC_PORT="${PUBLIC_PORT:-80}"
USE_TLS="${USE_TLS:-false}"
ADMINER_SUBDOMAIN="${ADMINER_SUBDOMAIN:-adminer}"
UMAMI_SUBDOMAIN="${UMAMI_SUBDOMAIN:-analytics}"

if [ "$USE_TLS" = "true" ]; then
    SCHEME="https"
    DEFAULT_PORT="443"
else
    SCHEME="http"
    DEFAULT_PORT="80"
fi

if [ "$PUBLIC_PORT" = "$DEFAULT_PORT" ]; then
    PORT_SUFFIX=""
else
    PORT_SUFFIX=":$PUBLIC_PORT"
fi

APP_URL="${SCHEME}://${PUBLIC_WEBSITE_HOST}${PORT_SUFFIX}"
API_DOCS_URL="${APP_URL}/api/docs"
STATIC_URL="${SCHEME}://static.${PUBLIC_WEBSITE_HOST}${PORT_SUFFIX}"
ADMINER_URL="${SCHEME}://${ADMINER_SUBDOMAIN}.${PUBLIC_WEBSITE_HOST}${PORT_SUFFIX}"
UMAMI_URL="${SCHEME}://${UMAMI_SUBDOMAIN}.${PUBLIC_WEBSITE_HOST}${PORT_SUFFIX}"

flag() {
    if [ "${1:-false}" = "true" ]; then
        echo -e "${GREEN}on${NC}"
    else
        echo -e "${YELLOW}off${NC}"
    fi
}

label() {
    printf "  ${BLUE}%-10s${NC} %s\n" "$1" "$2"
}

echo
echo -e "${GREEN}────────────────────────────────────────────────────────────${NC}"
echo -e "${GREEN} Stack ready (${MODE})${NC}"
echo -e "${GREEN}────────────────────────────────────────────────────────────${NC}"
label "App"       "$APP_URL"
label "API docs"  "$API_DOCS_URL"
label "Static"    "$STATIC_URL"
label "Adminer"   "$ADMINER_URL"
label "Analytics" "$UMAMI_URL"
if [ "$MODE" = "dev" ]; then
    label "Traefik"   "http://localhost:${TRAEFIK_DASHBOARD_PORT:-8080}"
fi
echo
printf "  ${BLUE}Features${NC}  stripe=%b  orgs=%b  oauth=%b  llm=%b\n" \
    "$(flag "${STRIPE_ENABLED:-false}")" \
    "$(flag "${ORGANIZATIONS_ENABLED:-false}")" \
    "$(flag "${OAUTH_ENABLED:-false}")" \
    "$(flag "${LLM_ENABLED:-false}")"
echo
echo -e "  ${BLUE}Tip${NC}       'npm run info' to reprint · 'npm run logs' to re-tail · 'npm run stop' to stop"
echo -e "${GREEN}────────────────────────────────────────────────────────────${NC}"
echo
