#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
# Shared utilities for starterpack scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Prompt for required input
# Usage: result=$(prompt_required "Enter project name" "default")
prompt_required() {
    local prompt="$1"
    local default="$2"
    local value=""

    while [ -z "$value" ]; do
        if [ -n "$default" ]; then
            read -rp "$prompt [$default]: " value
            value="${value:-$default}"
        else
            read -rp "$prompt: " value
        fi

        if [ -z "$value" ]; then
            print_error "This field is required"
        fi
    done

    echo "$value"
}

# Prompt for optional input with default
# Usage: result=$(prompt_optional "Enter domain" "localhost")
prompt_optional() {
    local prompt="$1"
    local default="$2"
    local value=""

    read -rp "$prompt [$default]: " value
    echo "${value:-$default}"
}

# Prompt yes/no
# Usage: if prompt_confirm "Enable TLS?" "n"; then ... fi
prompt_confirm() {
    local prompt="$1"
    local default="${2:-n}"
    local yn_hint="[y/N]"
    local value=""

    if [ "$default" = "y" ]; then
        yn_hint="[Y/n]"
    fi

    read -rp "$prompt $yn_hint: " value
    value="${value:-$default}"

    case "$value" in
        [Yy]* ) return 0;;
        * ) return 1;;
    esac
}

# Generate a random secret
generate_secret() {
    head -c 32 /dev/urandom | sha256sum | cut -d" " -f1
}

# Slugify a string (lowercase, replace spaces/special chars with dashes)
# Usage: slug=$(slugify "My Project Name")  # Returns: my-project-name
slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g'
}

# Validate project name (valid for docker compose project name)
# Must start with a letter, contain only lowercase letters, numbers, dashes, underscores
validate_project_name() {
    local name="$1"
    if [[ "$name" =~ ^[a-z][a-z0-9_-]*$ ]]; then
        return 0
    fi
    return 1
}
