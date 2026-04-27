#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

# Validates bidirectional consistency between:
# 1. Files containing "STARTERPACK CORE" header
# 2. Files referenced in starter-pack-files.txt

set -e

cd "$(dirname "$0")/../.."

MANIFEST="starter-pack-files.txt"
HEADER_PATTERN="STARTERPACK CORE"

# Files that can't have comments or shouldn't have them
EXCEPTIONS=(
    "package.json"
    "package-lock.json"
    "core-en.json"
    "core-fr.json"
    ".starterpack-version"
    ".mcp.json"
)

# Parse manifest entry to extract path and mode
# Format: path/to/file.ts:mode or just path/to/file.ts
parse_manifest_entry() {
    local entry="$1"

    if [[ "$entry" == *":sync" ]]; then
        echo "${entry%:sync}|sync"
    elif [[ "$entry" == *":template" ]]; then
        echo "${entry%:template}|template"
    elif [[ "$entry" == *":delete" ]]; then
        echo "${entry%:delete}|delete"
    else
        echo "$entry|sync"
    fi
}

# Check if a filename is in the exceptions list
is_exception() {
    local file="$1"
    local basename
    basename=$(basename "$file")
    for exc in "${EXCEPTIONS[@]}"; do
        if [[ "$basename" == "$exc" ]]; then
            return 0
        fi
    done
    return 1
}

# Expand a glob pattern and return matching files (not directories)
expand_pattern() {
    local pattern="$1"
    # Use bash globbing
    shopt -s nullglob globstar
    for file in $pattern; do
        if [[ -f "$file" ]]; then
            echo "$file"
        fi
    done
}

# Get all sync-mode files from manifest (expanded from patterns)
# Only returns files that need the STARTERPACK CORE header
get_manifest_sync_files() {
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and blank lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        # Parse entry to get path and mode
        local parsed
        parsed=$(parse_manifest_entry "$line")
        local pattern="${parsed%|*}"
        local mode="${parsed#*|}"

        # Only include sync mode files (they need CORE header)
        if [[ "$mode" == "sync" ]]; then
            expand_pattern "$pattern"
        fi
    done < "$MANIFEST"
}

# Get all files from manifest (all modes, for matching check)
get_all_manifest_patterns() {
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and blank lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        # Parse entry to get path only (strip mode)
        local parsed
        parsed=$(parse_manifest_entry "$line")
        local pattern="${parsed%|*}"

        echo "$pattern"
    done < "$MANIFEST"
}

# Get all files containing the header pattern in first 4 lines
get_files_with_header() {
    local extensions=("sh" "py" "ts" "vue" "css" "yml" "yaml" "sql" "md" "json" "txt" "toml" "html")
    local exclude_dirs=(".git" "node_modules" "__pycache__" ".nuxt" ".output")

    # Build find command
    local find_cmd="find . -type f \\("
    for i in "${!extensions[@]}"; do
        if [[ $i -gt 0 ]]; then
            find_cmd+=" -o"
        fi
        find_cmd+=" -name \"*.${extensions[$i]}\""
    done
    find_cmd+=" -o -name \"Dockerfile\" \\)"

    for dir in "${exclude_dirs[@]}"; do
        find_cmd+=" -not -path \"*/$dir/*\""
    done

    # Find files and check first 4 lines for header
    eval "$find_cmd" 2>/dev/null | while read -r file; do
        if head -n 4 "$file" 2>/dev/null | grep -q "$HEADER_PATTERN"; then
            echo "$file" | sed 's|^\./||'
        fi
    done | sort -u
}

# Check if a file matches any pattern in the manifest (any mode)
matches_manifest() {
    local file="$1"
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and blank lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        # Parse entry to get path (strip mode)
        local parsed
        parsed=$(parse_manifest_entry "$line")
        local pattern="${parsed%|*}"

        # Check if the file matches this pattern
        # For exact matches
        if [[ "$file" == "$pattern" ]]; then
            return 0
        fi

        # For glob patterns, expand and check
        shopt -s nullglob globstar
        for match in $pattern; do
            if [[ "$file" == "$match" ]]; then
                return 0
            fi
        done
    done < "$MANIFEST"
    return 1
}

echo "Validating starterpack core files consistency..."
echo

errors=0

# Check 1: All sync-mode manifest files should have the header (except exceptions)
echo "Check 1: Sync-mode files in manifest should have STARTERPACK CORE header"
manifest_files=$(get_manifest_sync_files | sort -u)
manifest_count=0
missing_header=()

while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    manifest_count=$((manifest_count + 1))

    if is_exception "$file"; then
        continue
    fi

    if ! head -n 4 "$file" 2>/dev/null | grep -q "$HEADER_PATTERN"; then
        missing_header+=("$file")
    fi
done <<< "$manifest_files"

if [[ ${#missing_header[@]} -eq 0 ]]; then
    echo "  ✓ All $manifest_count manifest files have the header (or are exceptions)"
else
    echo "  ✗ Missing STARTERPACK CORE header:"
    for file in "${missing_header[@]}"; do
        echo "    - $file"
    done
    errors=1
fi

echo

# Check 2: All files with header should be in manifest
echo "Check 2: Files with STARTERPACK CORE header should be in manifest"
files_with_header=$(get_files_with_header)
header_count=$(echo "$files_with_header" | grep -c . || echo 0)
orphaned=()

while IFS= read -r file; do
    [[ -z "$file" ]] && continue

    if ! matches_manifest "$file"; then
        orphaned+=("$file")
    fi
done <<< "$files_with_header"

if [[ ${#orphaned[@]} -eq 0 ]]; then
    echo "  ✓ All $header_count files with header are in manifest"
else
    echo "  ✗ Not in manifest but has STARTERPACK CORE header:"
    for file in "${orphaned[@]}"; do
        echo "    - $file"
    done
    errors=1
fi

echo

if [[ $errors -eq 0 ]]; then
    echo "All checks passed!"
    exit 0
else
    echo "Validation failed. Please fix the issues above."
    exit 1
fi
