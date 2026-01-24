#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
#
# Auto-install script for Website Starter Pack
# Usage: bash <(curl -sSL https://raw.githubusercontent.com/7PH/website-starter-pack/master/scripts/_core/auto-install.sh)

set -e

REPO_URL="https://github.com/7PH/website-starter-pack.git"

echo ""
echo "Website Starter Pack - Auto Install"
echo ""

# Only prompt needed: project directory name
read -rp "Project name: " PROJECT_NAME
PROJECT_SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g')

if [ -z "$PROJECT_SLUG" ]; then
    echo "Error: Project name is required"
    exit 1
fi

if [ -d "$PROJECT_SLUG" ]; then
    echo "Error: Directory '$PROJECT_SLUG' already exists"
    exit 1
fi

echo ""
echo "Cloning repository into '$PROJECT_SLUG'..."
git clone --depth 1 "$REPO_URL" "$PROJECT_SLUG"
cd "$PROJECT_SLUG"

# Start fresh git history
rm -rf .git
git init

# Install dependencies and configure
npm install
npx envfill

# Show next steps
echo ""
echo "Project '$PROJECT_SLUG' created successfully!"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_SLUG"
echo "  npm run dev"
echo ""
