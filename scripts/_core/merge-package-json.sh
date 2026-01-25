#!/bin/sh
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

# Merges package.core.json with package.app.json to produce package.json
# Usage: merge-package-json.sh <directory>
# Example: merge-package-json.sh app/frontend
#
# This script is called from npm preinstall hooks. It gracefully skips
# when run in contexts where merging isn't needed (e.g., Docker builds).

set -e

DIR="${1:-.}"

CORE_FILE="$DIR/package.core.json"
APP_FILE="$DIR/package.app.json"
OUTPUT_FILE="$DIR/package.json"

# Skip silently if core file doesn't exist (e.g., in Docker where only package.json is copied)
if [ ! -f "$CORE_FILE" ]; then
    exit 0
fi

# Check if jq is available
if ! command -v jq > /dev/null 2>&1; then
    echo "Warning: jq not found, skipping package.json merge." >&2
    exit 0
fi

# If app file exists, merge core + app; otherwise just use core
if [ -f "$APP_FILE" ]; then
    # Deep merge: app values override core values
    # For dependencies/devDependencies, merge objects (app adds to or overrides core)
    # For scripts, merge objects (app adds to or overrides core)
    # For other fields, app completely overrides core
    # Note: _comment is removed from final output (it's just for documentation)
    MERGED=$(jq -s '
        def deep_merge:
            if (.[0] | type) == "object" and (.[1] | type) == "object" then
                .[0] * .[1]
            else
                .[1] // .[0]
            end;
        [.[0], .[1]] | deep_merge | del(._comment)
    ' "$CORE_FILE" "$APP_FILE")
else
    # Remove _comment from core-only output too
    MERGED=$(jq 'del(._comment)' "$CORE_FILE")
fi

# Add generated notice and write output
FINAL=$(echo "$MERGED" | jq '{
    "_generated": "DO NOT EDIT. This file is generated from package.core.json + package.app.json. Run: npm install to regenerate."
} + .')

echo "$FINAL" > "$OUTPUT_FILE"

echo "Merged package.json in $DIR"
