#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
#
# Auto-install script for Website Starter Pack
# Usage: bash <(curl -sSL https://raw.githubusercontent.com/7PH/website-starter-pack/master/scripts/_core/auto-install.sh)

set -e

REPO_URL="https://github.com/7PH/website-starter-pack.git"
UTILS_URL="https://raw.githubusercontent.com/7PH/website-starter-pack/master/scripts/_core/utils.sh"

# Download and source utilities
UTILS_TMP=$(mktemp)
trap "rm -f $UTILS_TMP" EXIT
curl -sSL "$UTILS_URL" > "$UTILS_TMP"
source "$UTILS_TMP"

# Banner
echo ""
print_info "Website Starter Pack - Auto Install"
echo ""

# Prompts (6 total)
PROJECT_NAME=$(prompt_required "Project name")
PROJECT_SLUG=$(slugify "$PROJECT_NAME")
while ! validate_project_name "$PROJECT_SLUG"; do
    print_error "Invalid name. Use lowercase letters, numbers, dashes only. Must start with a letter."
    PROJECT_NAME=$(prompt_required "Project name")
    PROJECT_SLUG=$(slugify "$PROJECT_NAME")
done

APP_NAME=$(prompt_optional "App display name" "$PROJECT_NAME")
DOMAIN=$(prompt_optional "Domain" "localhost")

if prompt_confirm "Enable TLS/HTTPS?" "n"; then
    USE_TLS="true"
    PUBLIC_PORT="443"
    PUBLIC_URL="https://$DOMAIN"
else
    USE_TLS=""
    PUBLIC_PORT="80"
    PUBLIC_URL="http://$DOMAIN"
fi

DEFAULT_LOCALE=$(prompt_optional "Default locale" "en")
ADMIN_EMAIL=$(prompt_optional "Admin email" "")

# Check if directory already exists
if [ -d "$PROJECT_SLUG" ]; then
    print_error "Directory '$PROJECT_SLUG' already exists"
    exit 1
fi

# Clone repository
echo ""
print_info "Cloning repository into '$PROJECT_SLUG'..."
git clone --depth 1 "$REPO_URL" "$PROJECT_SLUG"
cd "$PROJECT_SLUG"

# Remove git history to start fresh
rm -rf .git
git init

# Export variables for setup.sh
export STARTERPACK_PROJECT_NAME="$PROJECT_SLUG"
export STARTERPACK_APP_NAME="$APP_NAME"
export STARTERPACK_DOMAIN="$DOMAIN"
export STARTERPACK_USE_TLS="$USE_TLS"
export STARTERPACK_PUBLIC_PORT="$PUBLIC_PORT"
export STARTERPACK_PUBLIC_URL="$PUBLIC_URL"
export STARTERPACK_DEFAULT_LOCALE="$DEFAULT_LOCALE"
export STARTERPACK_ADMIN_EMAIL="$ADMIN_EMAIL"

# Run setup
bash scripts/_core/setup.sh

# Show next steps
echo ""
print_success "Project '$PROJECT_SLUG' created successfully!"
echo ""
print_info "Next steps:"
echo "  cd $PROJECT_SLUG"
echo "  npm run dev"
echo ""
