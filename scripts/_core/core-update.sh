#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Config
MANIFEST="starter-pack-files.txt"
TEMP_DIR=$(mktemp -d)
UPSTREAM_DIR="$TEMP_DIR/starterpack"

# Cleanup on exit
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Arrays to track changes
ADDED_FILES=()
MODIFIED_FILES=()
DELETED_FILES=()

#######################################
# Check prerequisites
#######################################
check_prerequisites() {
    # Check git is clean
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${RED}Error: Git working directory is not clean.${NC}"
        echo "Please commit or stash your changes before running this script."
        exit 1
    fi

    # Check env var
    if [ -z "$STARTER_PACK_GIT_REPOSITORY" ]; then
        echo -e "${RED}Error: STARTER_PACK_GIT_REPOSITORY environment variable is not set.${NC}"
        exit 1
    fi

    # Check manifest exists
    if [ ! -f "$MANIFEST" ]; then
        echo -e "${RED}Error: Manifest file '$MANIFEST' not found.${NC}"
        exit 1
    fi
}

#######################################
# Clone starterpack to temp folder
#######################################
clone_upstream() {
    echo -e "${BLUE}Cloning starterpack repository...${NC}"
    git clone --depth 1 --branch master "$STARTER_PACK_GIT_REPOSITORY" "$UPSTREAM_DIR" 2>/dev/null
    echo -e "${GREEN}Done.${NC}"
}

#######################################
# Expand a pattern to list of files
# Handles both exact paths and wildcards
#######################################
expand_pattern() {
    local pattern="$1"
    local base_dir="$2"

    if [[ "$pattern" == *"*"* ]]; then
        # Pattern contains wildcard - expand it
        # Convert glob pattern to find-compatible pattern
        local dir=$(dirname "$pattern")
        local file_pattern=$(basename "$pattern")

        if [ -d "$base_dir/$dir" ]; then
            find "$base_dir/$dir" -maxdepth 1 -name "$file_pattern" -type f 2>/dev/null | \
                sed "s|^$base_dir/||"
        fi
    else
        # Exact path
        if [ -f "$base_dir/$pattern" ]; then
            echo "$pattern"
        elif [ -d "$base_dir/$pattern" ]; then
            # It's a directory - list all files recursively
            find "$base_dir/$pattern" -type f 2>/dev/null | sed "s|^$base_dir/||"
        fi
    fi
}

#######################################
# Read manifest and expand all patterns
#######################################
get_upstream_files() {
    local files=()

    while IFS= read -r line || [[ -n "$line" ]]; do
        # Trim whitespace and skip empty lines or comments
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -z "$line" || "$line" == \#* ]]; then
            continue
        fi

        # Expand pattern and add to files array
        while IFS= read -r file; do
            if [ -n "$file" ]; then
                files+=("$file")
            fi
        done < <(expand_pattern "$line" "$UPSTREAM_DIR")
    done < "$UPSTREAM_DIR/$MANIFEST"

    printf '%s\n' "${files[@]}" | sort -u
}

#######################################
# Get current local files from manifest
#######################################
get_local_files() {
    local files=()

    while IFS= read -r line || [[ -n "$line" ]]; do
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -z "$line" || "$line" == \#* ]]; then
            continue
        fi

        while IFS= read -r file; do
            if [ -n "$file" ]; then
                files+=("$file")
            fi
        done < <(expand_pattern "$line" ".")
    done < "$MANIFEST"

    printf '%s\n' "${files[@]}" | sort -u
}

#######################################
# Compare files and categorize changes
#######################################
compare_files() {
    echo -e "${BLUE}Comparing files...${NC}"

    # Get file lists
    local upstream_files=$(get_upstream_files)
    local local_files=$(get_local_files)

    # Check each upstream file
    while IFS= read -r file; do
        [ -z "$file" ] && continue

        if [ ! -f "$file" ]; then
            # File doesn't exist locally - it's new
            ADDED_FILES+=("$file")
        elif ! diff -q "$file" "$UPSTREAM_DIR/$file" >/dev/null 2>&1; then
            # File exists but is different
            MODIFIED_FILES+=("$file")
        fi
    done <<< "$upstream_files"

    # Check for deleted files (in local but not in upstream)
    while IFS= read -r file; do
        [ -z "$file" ] && continue

        if [ ! -f "$UPSTREAM_DIR/$file" ]; then
            DELETED_FILES+=("$file")
        fi
    done <<< "$local_files"
}

#######################################
# Show summary of changes
#######################################
show_summary() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}           STARTERPACK UPDATE          ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""

    local total=$((${#ADDED_FILES[@]} + ${#MODIFIED_FILES[@]} + ${#DELETED_FILES[@]}))

    if [ $total -eq 0 ]; then
        echo -e "${GREEN}Everything is up to date!${NC}"
        return 1
    fi

    if [ ${#ADDED_FILES[@]} -gt 0 ]; then
        echo -e "${GREEN}+ ${#ADDED_FILES[@]} file(s) to add:${NC}"
        for file in "${ADDED_FILES[@]}"; do
            echo -e "    ${GREEN}+ $file${NC}"
        done
        echo ""
    fi

    if [ ${#MODIFIED_FILES[@]} -gt 0 ]; then
        echo -e "${YELLOW}~ ${#MODIFIED_FILES[@]} file(s) to update:${NC}"
        for file in "${MODIFIED_FILES[@]}"; do
            echo -e "    ${YELLOW}~ $file${NC}"
        done
        echo ""
    fi

    if [ ${#DELETED_FILES[@]} -gt 0 ]; then
        echo -e "${RED}- ${#DELETED_FILES[@]} file(s) to remove:${NC}"
        for file in "${DELETED_FILES[@]}"; do
            echo -e "    ${RED}- $file${NC}"
        done
        echo ""
    fi

    return 0
}

#######################################
# Show diffs for modified files
#######################################
show_diffs() {
    if [ ${#MODIFIED_FILES[@]} -eq 0 ]; then
        return
    fi

    echo -e "${BLUE}───────────────────────────────────────${NC}"
    echo -e "${BLUE}              CHANGES                  ${NC}"
    echo -e "${BLUE}───────────────────────────────────────${NC}"

    for file in "${MODIFIED_FILES[@]}"; do
        echo ""
        echo -e "${YELLOW}==> $file${NC}"
        diff --color=always -u "$file" "$UPSTREAM_DIR/$file" 2>/dev/null || true
    done

    echo ""
}

#######################################
# Apply all changes
#######################################
apply_changes() {
    echo -e "${BLUE}Applying changes...${NC}"

    # Add new files
    for file in "${ADDED_FILES[@]}"; do
        mkdir -p "$(dirname "$file")"
        cp "$UPSTREAM_DIR/$file" "$file"
        echo -e "${GREEN}+ Added: $file${NC}"
    done

    # Update modified files
    for file in "${MODIFIED_FILES[@]}"; do
        cp "$UPSTREAM_DIR/$file" "$file"
        echo -e "${YELLOW}~ Updated: $file${NC}"
    done

    # Delete removed files
    for file in "${DELETED_FILES[@]}"; do
        rm -f "$file"
        echo -e "${RED}- Removed: $file${NC}"
    done

    echo ""
    echo -e "${GREEN}Update complete!${NC}"
}

#######################################
# Main
#######################################
main() {
    check_prerequisites
    clone_upstream
    compare_files

    if ! show_summary; then
        exit 0
    fi

    show_diffs

    echo -e "${BLUE}───────────────────────────────────────${NC}"
    read -p "Apply these changes? [y/N] " confirm

    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi

    echo ""
    apply_changes
}

main "$@"
