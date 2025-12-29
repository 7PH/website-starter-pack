#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

# Source utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

# Create .env from .env.template if not exists
if [ ! -f .env ]; then
    print_info "Creating .env file..."

    # Use env vars if set (from auto-install), otherwise prompt interactively
    PROJECT_NAME="${STARTERPACK_PROJECT_NAME:-}"
    if [ -z "$PROJECT_NAME" ]; then
        PROJECT_NAME=$(prompt_required "Project name" "starterpack")
        PROJECT_NAME=$(slugify "$PROJECT_NAME")
        while ! validate_project_name "$PROJECT_NAME"; do
            print_error "Invalid name. Use lowercase letters, numbers, dashes only. Must start with a letter."
            PROJECT_NAME=$(prompt_required "Project name" "starterpack")
            PROJECT_NAME=$(slugify "$PROJECT_NAME")
        done
    fi

    APP_NAME="${STARTERPACK_APP_NAME:-}"
    if [ -z "$APP_NAME" ]; then
        APP_NAME=$(prompt_optional "App display name" "$PROJECT_NAME")
    fi

    DOMAIN="${STARTERPACK_DOMAIN:-}"
    if [ -z "$DOMAIN" ]; then
        DOMAIN=$(prompt_optional "Domain" "localhost")
    fi

    USE_TLS="${STARTERPACK_USE_TLS:-}"
    PUBLIC_PORT="${STARTERPACK_PUBLIC_PORT:-}"
    PUBLIC_URL="${STARTERPACK_PUBLIC_URL:-}"
    if [ -z "${STARTERPACK_USE_TLS+x}" ]; then
        if prompt_confirm "Enable TLS/HTTPS?" "n"; then
            USE_TLS="true"
            PUBLIC_PORT="443"
            PUBLIC_URL="https://$DOMAIN"
        else
            USE_TLS=""
            PUBLIC_PORT="80"
            PUBLIC_URL="http://$DOMAIN"
        fi
    fi

    DEFAULT_LOCALE="${STARTERPACK_DEFAULT_LOCALE:-}"
    if [ -z "$DEFAULT_LOCALE" ]; then
        DEFAULT_LOCALE=$(prompt_optional "Default locale" "en")
    fi

    ADMIN_EMAIL="${STARTERPACK_ADMIN_EMAIL:-}"
    if [ -z "$ADMIN_EMAIL" ]; then
        ADMIN_EMAIL=$(prompt_optional "Admin email" "")
    fi

    # Generate .env file
    sed \
        -e "s/\$USER_NAME/$(id -un)/g" \
        -e "s/\$USER_ID/$(id -u)/g" \
        -e "s/\$GROUP_ID/$(id -g)/g" \
        -e "s/\$PROJECT_NAME/$PROJECT_NAME/g" \
        -e "s/\$APP_NAME/$APP_NAME/g" \
        -e "s/\$DOMAIN/$DOMAIN/g" \
        -e "s/\$USE_TLS/$USE_TLS/g" \
        -e "s/\$PUBLIC_PORT/$PUBLIC_PORT/g" \
        -e "s|\$PUBLIC_URL|$PUBLIC_URL|g" \
        -e "s/\$DEFAULT_LOCALE/$DEFAULT_LOCALE/g" \
        -e "s/\$ADMIN_EMAIL/$ADMIN_EMAIL/g" \
        -e "s/\$TOKEN_HASH_SECRET/$(generate_secret)/g" \
        -e "s/\$USERS_PASSWORD_HASH_SECRET_KEY/$(generate_secret)/g" \
        -e "s/\$APP_DB_PASSWORD/$(generate_secret)/g" \
        -e "s/\$UMAMI_DB_PASSWORD/$(generate_secret)/g" \
        -e "s/\$UMAMI_APP_SECRET/$(generate_secret)/g" \
        .env.template \
        > .env

    print_success ".env file created"
fi

# Create required directories (db/umami data dirs are created by Docker)
print_info "Creating directories..."

mkdir -p backups

mkdir -p static

print_success "Setup complete!"
