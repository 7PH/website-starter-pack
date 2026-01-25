#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

print_info "Configuring environment..."

if [ -n "$CI" ]; then
    npx envfill --defaults
else
    npx envfill
fi

print_success ".env file configured"

print_info "Creating directories..."
mkdir -p backups static

print_info "Merging package.json files..."
bash "$SCRIPT_DIR/merge-package-json.sh" .
bash "$SCRIPT_DIR/merge-package-json.sh" app/frontend
print_success "Package files merged"

print_success "Setup complete!"
