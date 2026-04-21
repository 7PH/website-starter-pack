#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

set -e

# Load .env file if it exists
if [ -f .env ]; then
    set -a && source .env && set +a
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Config
MANIFEST="starter-pack-files.txt"
VERSION_FILE=".starterpack-version"
TEMP_DIR=$(mktemp -d)
UPSTREAM_DIR="$TEMP_DIR/starterpack"

# Parse command line arguments
ANALYZE_ONLY=false
LIST_DIVERGENCES=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --analyze)
            ANALYZE_ONLY=true
            shift
            ;;
        --list-divergences)
            LIST_DIVERGENCES=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--analyze | --list-divergences]"
            echo "  --analyze           Show upgrade analysis without applying changes"
            echo "  --list-divergences  List core files that diverge from upstream master (audit only)"
            exit 1
            ;;
    esac
done

# Cleanup on exit
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Arrays to track changes by mode
# Sync mode: full overwrite
SYNC_ADDED=()
SYNC_MODIFIED=()
SYNC_REMOVED=()

# Template mode: create if missing, never overwrite
TEMPLATE_CREATED=()
TEMPLATE_SKIPPED=()

# Delete mode: remove if exists
DELETE_REMOVED=()
DELETE_SKIPPED=()

# Associative array to store file modes from manifest
declare -A FILE_MODES
# Global array populated by get_upstream_files (avoids subshell losing FILE_MODES)
UPSTREAM_FILES=()

#######################################
# Reset comparison arrays for re-comparison
#######################################
reset_comparison_arrays() {
    SYNC_ADDED=()
    SYNC_MODIFIED=()
    SYNC_REMOVED=()
    TEMPLATE_CREATED=()
    TEMPLATE_SKIPPED=()
    DELETE_REMOVED=()
    DELETE_SKIPPED=()
    FILE_MODES=()
    declare -gA FILE_MODES
    UPSTREAM_FILES=()
}

#######################################
# Check if manifest file is in the list of files to sync
#######################################
manifest_needs_sync() {
    for file in "${SYNC_MODIFIED[@]}" "${SYNC_ADDED[@]}"; do
        if [ "$file" = "$MANIFEST" ]; then
            return 0
        fi
    done
    return 1
}

#######################################
# Parse manifest entry to extract path and mode
# Format: path/to/file.ts:mode or just path/to/file.ts
# Valid modes: sync (default), template, delete
#######################################
parse_manifest_entry() {
    local entry="$1"
    local path mode

    # Check for known mode suffixes
    if [[ "$entry" == *":sync" ]]; then
        path="${entry%:sync}"
        mode="sync"
    elif [[ "$entry" == *":template" ]]; then
        path="${entry%:template}"
        mode="template"
    elif [[ "$entry" == *":delete" ]]; then
        path="${entry%:delete}"
        mode="delete"
    else
        path="$entry"
        mode="sync"
    fi

    echo "$path|$mode"
}

#######################################
# Check prerequisites
#######################################
check_prerequisites() {
    # Check git is clean (skipped for read-only audits)
    if [ "$LIST_DIVERGENCES" != true ] && [ -n "$(git status --porcelain 2>/dev/null)" ]; then
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
# Also populates FILE_MODES associative array
#######################################
get_upstream_files() {
    # Populates global UPSTREAM_FILES array and FILE_MODES.
    # Must NOT be called in a subshell or FILE_MODES changes will be lost.
    UPSTREAM_FILES=()
    local -A seen=()

    while IFS= read -r line || [[ -n "$line" ]]; do
        # Trim whitespace and skip empty lines or comments
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -z "$line" || "$line" == \#* ]]; then
            continue
        fi

        # Parse entry to get path and mode
        local parsed=$(parse_manifest_entry "$line")
        local pattern="${parsed%|*}"
        local mode="${parsed#*|}"

        # Expand pattern and add to files array with mode
        while IFS= read -r file; do
            if [ -n "$file" ] && [ -z "${seen[$file]}" ]; then
                seen["$file"]=1
                UPSTREAM_FILES+=("$file")
                FILE_MODES["$file"]="$mode"
            fi
        done < <(expand_pattern "$pattern" "$UPSTREAM_DIR")
    done < "$UPSTREAM_DIR/$MANIFEST"

    # Sort in-place
    IFS=$'\n' read -r -d '' -a UPSTREAM_FILES < <(printf '%s\n' "${UPSTREAM_FILES[@]}" | sort -u && printf '\0')
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

        # Parse entry to strip mode suffix (same as get_upstream_files)
        local parsed=$(parse_manifest_entry "$line")
        local pattern="${parsed%|*}"

        while IFS= read -r file; do
            if [ -n "$file" ]; then
                files+=("$file")
            fi
        done < <(expand_pattern "$pattern" ".")
    done < "$MANIFEST"

    printf '%s\n' "${files[@]}" | sort -u
}

#######################################
# Get version from file, defaulting to 0.0.0
#######################################
get_version() {
    local dir="$1"
    local version_path="$dir/$VERSION_FILE"
    if [ -f "$version_path" ]; then
        cat "$version_path" | tr -d '[:space:]'
    else
        echo "0.0.0"
    fi
}

#######################################
# Compare version strings (returns 0 if v1 < v2, 1 otherwise)
#######################################
version_lt() {
    local v1="$1"
    local v2="$2"
    [ "$v1" != "$v2" ] && [ "$(printf '%s\n' "$v1" "$v2" | sort -V | head -n1)" = "$v1" ]
}

#######################################
# Get list of upgrade note files between versions
#######################################
get_upgrade_notes_between() {
    local from_version="$1"
    local to_version="$2"
    local upgrades_dir="$UPSTREAM_DIR/docs/upgrades"

    if [ ! -d "$upgrades_dir" ]; then
        return
    fi

    # Find all version files and filter those between from and to
    for file in "$upgrades_dir"/v*.md; do
        [ -f "$file" ] || continue
        local filename=$(basename "$file")
        # Extract version from filename (v1.0.0.md -> 1.0.0)
        local file_version="${filename#v}"
        file_version="${file_version%.md}"

        # Include if version > from_version AND version <= to_version
        if version_lt "$from_version" "$file_version" && ! version_lt "$to_version" "$file_version"; then
            echo "$file"
        fi
    done | sort -V
}

#######################################
# Display upgrade notes between versions
#######################################
show_upgrade_notes() {
    local from_version="$1"
    local to_version="$2"

    local notes_files=$(get_upgrade_notes_between "$from_version" "$to_version")

    if [ -z "$notes_files" ]; then
        return
    fi

    echo ""
    echo -e "${CYAN}=== UPGRADE NOTES ===${NC}"
    echo ""

    while IFS= read -r file; do
        [ -z "$file" ] && continue
        echo -e "${BLUE}--- $(basename "$file") ---${NC}"
        cat "$file"
        echo ""
    done <<< "$notes_files"
}

#######################################
# Detect and display local modifications to sync files
# Only shows modifications that will be overwritten by upgrade
#######################################
detect_local_modifications() {
    local has_modifications=false

    # First pass: check if there are any modifications
    for file in "${SYNC_MODIFIED[@]}"; do
        if [ -f "$file" ] && ! git diff --quiet HEAD -- "$file" 2>/dev/null; then
            has_modifications=true
            break
        fi
    done

    if [ "$has_modifications" = false ]; then
        return
    fi

    echo ""
    echo -e "${YELLOW}=== LOCAL MODIFICATIONS (will be overwritten) ===${NC}"
    echo ""

    for file in "${SYNC_MODIFIED[@]}"; do
        if [ -f "$file" ] && ! git diff --quiet HEAD -- "$file" 2>/dev/null; then
            echo -e "${YELLOW}--- $file ---${NC}"
            # Show diff between last commit and working tree
            # This shows what the user has modified locally
            git diff HEAD -- "$file" 2>/dev/null || true
            echo ""
        fi
    done
}

#######################################
# Show upstream changes for modified files
#######################################
show_upstream_changes() {
    if [ ${#SYNC_MODIFIED[@]} -eq 0 ]; then
        return
    fi

    echo ""
    echo -e "${CYAN}=== UPSTREAM CHANGES ===${NC}"
    echo ""

    for file in "${SYNC_MODIFIED[@]}"; do
        echo -e "${BLUE}--- $file ---${NC}"
        diff -u "$file" "$UPSTREAM_DIR/$file" 2>/dev/null || true
        echo ""
    done
}

#######################################
# Compare files and categorize changes
# Handles sync, template, and delete modes
#######################################
compare_files() {
    echo -e "${BLUE}Comparing files...${NC}"

    # get_upstream_files populates UPSTREAM_FILES and FILE_MODES globals.
    # It must be called directly (not in a subshell) so FILE_MODES is preserved.
    get_upstream_files
    local local_files
    local_files=$(get_local_files)

    # Process each upstream file based on its mode
    for file in "${UPSTREAM_FILES[@]}"; do
        [ -z "$file" ] && continue

        local mode="${FILE_MODES[$file]:-sync}"

        case "$mode" in
            sync)
                # Sync mode: track added/modified files
                if [ ! -f "$file" ]; then
                    SYNC_ADDED+=("$file")
                elif ! diff -q "$file" "$UPSTREAM_DIR/$file" >/dev/null 2>&1; then
                    SYNC_MODIFIED+=("$file")
                fi
                ;;
            template)
                # Template mode: create if missing, skip if exists
                if [ ! -f "$file" ]; then
                    TEMPLATE_CREATED+=("$file")
                else
                    TEMPLATE_SKIPPED+=("$file")
                fi
                ;;
            delete)
                # Delete mode: remove if exists
                if [ -f "$file" ]; then
                    DELETE_REMOVED+=("$file")
                else
                    DELETE_SKIPPED+=("$file")
                fi
                ;;
        esac
    done

    # Check for files removed from manifest (sync mode only)
    # These are files that exist locally but are no longer in upstream manifest
    while IFS= read -r file; do
        [ -z "$file" ] && continue

        # Only track removals for files that were previously synced
        if [ ! -f "$UPSTREAM_DIR/$file" ] && [ -z "${FILE_MODES[$file]}" ]; then
            SYNC_REMOVED+=("$file")
        fi
    done <<< "$local_files"
}

#######################################
# Check if there are any changes
#######################################
has_changes() {
    local total=$((
        ${#SYNC_ADDED[@]} + ${#SYNC_MODIFIED[@]} + ${#SYNC_REMOVED[@]} +
        ${#TEMPLATE_CREATED[@]} +
        ${#DELETE_REMOVED[@]}
    ))
    [ $total -gt 0 ]
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

    # Sync mode changes
    if [ ${#SYNC_ADDED[@]} -gt 0 ]; then
        echo -e "${GREEN}+ ${#SYNC_ADDED[@]} file(s) to add:${NC}"
        for file in "${SYNC_ADDED[@]}"; do
            echo -e "    ${GREEN}+ $file${NC}"
        done
        echo ""
    fi

    if [ ${#SYNC_MODIFIED[@]} -gt 0 ]; then
        echo -e "${YELLOW}~ ${#SYNC_MODIFIED[@]} file(s) to update:${NC}"
        for file in "${SYNC_MODIFIED[@]}"; do
            echo -e "    ${YELLOW}~ $file${NC}"
        done
        echo ""
    fi

    if [ ${#SYNC_REMOVED[@]} -gt 0 ]; then
        echo -e "${RED}- ${#SYNC_REMOVED[@]} file(s) to remove:${NC}"
        for file in "${SYNC_REMOVED[@]}"; do
            echo -e "    ${RED}- $file${NC}"
        done
        echo ""
    fi

    # Template mode changes
    if [ ${#TEMPLATE_CREATED[@]} -gt 0 ]; then
        echo -e "${GREEN}+ ${#TEMPLATE_CREATED[@]} template file(s) to create:${NC}"
        for file in "${TEMPLATE_CREATED[@]}"; do
            echo -e "    ${GREEN}+ $file${NC} (template)"
        done
        echo ""
    fi

    if [ ${#TEMPLATE_SKIPPED[@]} -gt 0 ]; then
        echo -e "${BLUE}  ${#TEMPLATE_SKIPPED[@]} template file(s) already exist (preserved):${NC}"
        for file in "${TEMPLATE_SKIPPED[@]}"; do
            echo -e "    ${BLUE}  $file${NC}"
        done
        echo ""
    fi

    # Delete mode changes
    if [ ${#DELETE_REMOVED[@]} -gt 0 ]; then
        echo -e "${RED}- ${#DELETE_REMOVED[@]} deprecated file(s) to remove:${NC}"
        for file in "${DELETE_REMOVED[@]}"; do
            echo -e "    ${RED}- $file${NC} (deprecated)"
        done
        echo ""
    fi
}

#######################################
# Show diffs for modified files
#######################################
show_diffs() {
    if [ ${#SYNC_MODIFIED[@]} -eq 0 ]; then
        return
    fi

    echo -e "${BLUE}───────────────────────────────────────${NC}"
    echo -e "${BLUE}              CHANGES                  ${NC}"
    echo -e "${BLUE}───────────────────────────────────────${NC}"

    for file in "${SYNC_MODIFIED[@]}"; do
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

    # Sync mode: add new files
    for file in "${SYNC_ADDED[@]}"; do
        mkdir -p "$(dirname "$file")"
        cp "$UPSTREAM_DIR/$file" "$file"
        echo -e "${GREEN}+ Added: $file${NC}"
    done

    # Sync mode: update modified files
    for file in "${SYNC_MODIFIED[@]}"; do
        cp "$UPSTREAM_DIR/$file" "$file"
        echo -e "${YELLOW}~ Updated: $file${NC}"
    done

    # Sync mode: delete removed files
    for file in "${SYNC_REMOVED[@]}"; do
        rm -f "$file"
        echo -e "${RED}- Removed: $file${NC}"
    done

    # Template mode: create missing files
    for file in "${TEMPLATE_CREATED[@]}"; do
        mkdir -p "$(dirname "$file")"
        cp "$UPSTREAM_DIR/$file" "$file"
        echo -e "${GREEN}+ Created template: $file${NC}"
    done

    # Delete mode: remove deprecated files
    for file in "${DELETE_REMOVED[@]}"; do
        rm -f "$file"
        echo -e "${RED}- Removed deprecated: $file${NC}"
    done

    echo ""
    echo -e "${GREEN}Update complete!${NC}"
}

#######################################
# Show version header
#######################################
show_version_header() {
    local local_version="$1"
    local upstream_version="$2"

    echo ""
    echo -e "${CYAN}=== STARTERPACK UPGRADE ANALYSIS ===${NC}"
    echo ""
    echo -e "Current version: ${YELLOW}$local_version${NC}"
    echo -e "Target version:  ${GREEN}$upstream_version${NC}"
}

#######################################
# Show files to be modified
#######################################
show_files_to_modify() {
    local total=$((${#SYNC_ADDED[@]} + ${#SYNC_MODIFIED[@]} + ${#SYNC_REMOVED[@]} + ${#TEMPLATE_CREATED[@]} + ${#DELETE_REMOVED[@]}))

    if [ $total -eq 0 ]; then
        return
    fi

    echo ""
    echo -e "${CYAN}=== FILES TO BE MODIFIED ===${NC}"
    echo ""

    for file in "${SYNC_ADDED[@]}"; do
        echo -e "${GREEN}+ $file${NC} (add)"
    done
    for file in "${SYNC_MODIFIED[@]}"; do
        echo -e "${YELLOW}~ $file${NC} (update)"
    done
    for file in "${SYNC_REMOVED[@]}"; do
        echo -e "${RED}- $file${NC} (remove)"
    done
    for file in "${TEMPLATE_CREATED[@]}"; do
        echo -e "${GREEN}+ $file${NC} (template)"
    done
    for file in "${DELETE_REMOVED[@]}"; do
        echo -e "${RED}- $file${NC} (deprecated)"
    done
}

#######################################
# List core files diverging from upstream master
# - Template-mode: customized locally, but upstream template may have evolved
# - Sync-mode: unexpected drift (should be fixed by re-running upgrade)
# Exits 0 if no divergence, 1 if any found.
#######################################
show_divergences() {
    local template_diverged=()
    local file

    # Diff each existing template file against upstream
    for file in "${TEMPLATE_SKIPPED[@]}"; do
        if ! diff -q "$file" "$UPSTREAM_DIR/$file" >/dev/null 2>&1; then
            template_diverged+=("$file")
        fi
    done

    local sync_count=${#SYNC_MODIFIED[@]}
    local template_count=${#template_diverged[@]}

    if [ $sync_count -eq 0 ] && [ $template_count -eq 0 ]; then
        echo ""
        echo -e "${GREEN}No divergences. All core files match upstream master.${NC}"
        return 0
    fi

    echo ""
    echo -e "${CYAN}=== DIVERGENCES FROM UPSTREAM MASTER ===${NC}"

    if [ $template_count -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Template files diverged from upstream (review for upstream updates):${NC}"
        for file in "${template_diverged[@]}"; do
            echo ""
            echo -e "${YELLOW}==> $file (template)${NC}"
            diff --color=always -u "$UPSTREAM_DIR/$file" "$file" 2>/dev/null || true
        done
    fi

    if [ $sync_count -gt 0 ]; then
        echo ""
        echo -e "${RED}Sync files drifted unexpectedly (re-run upgrade to fix):${NC}"
        for file in "${SYNC_MODIFIED[@]}"; do
            echo ""
            echo -e "${RED}==> $file (sync — unexpected drift)${NC}"
            diff --color=always -u "$UPSTREAM_DIR/$file" "$file" 2>/dev/null || true
        done
    fi

    echo ""
    echo -e "${BLUE}─── Divergence summary ───${NC}"
    if [ $template_count -gt 0 ]; then
        echo -e "${YELLOW}$template_count template file(s) diverged from upstream (review for upstream updates):${NC}"
        for file in "${template_diverged[@]}"; do
            echo -e "    ${YELLOW}~ $file${NC}"
        done
    fi
    if [ $sync_count -gt 0 ]; then
        echo -e "${RED}$sync_count sync file(s) drifted unexpectedly (re-run upgrade to fix):${NC}"
        for file in "${SYNC_MODIFIED[@]}"; do
            echo -e "    ${RED}~ $file${NC}"
        done
    fi

    return 1
}

#######################################
# Main
#######################################
main() {
    check_prerequisites
    clone_upstream

    # Get versions
    LOCAL_VERSION=$(get_version ".")
    UPSTREAM_VERSION=$(get_version "$UPSTREAM_DIR")

    # First pass: compare files
    compare_files

    # List-divergences mode: pure audit, don't mutate local state.
    # Use the local manifest as-is (skip the manifest re-sync below).
    if [ "$LIST_DIVERGENCES" = true ]; then
        show_divergences
        exit $?
    fi

    # If manifest itself changed, sync it first and re-compare
    # This ensures new files added to the manifest are detected in a single run
    if manifest_needs_sync; then
        echo -e "${YELLOW}Manifest changed - syncing first to detect all file changes...${NC}"

        # Sync manifest
        mkdir -p "$(dirname "$MANIFEST")"
        cp "$UPSTREAM_DIR/$MANIFEST" "$MANIFEST"

        # Reset and re-compare with updated manifest
        reset_comparison_arrays
        compare_files
    fi

    if [ "$ANALYZE_ONLY" = true ]; then
        # Analyze mode: show detailed analysis for AI/human review
        show_version_header "$LOCAL_VERSION" "$UPSTREAM_VERSION"

        if [ "$LOCAL_VERSION" != "$UPSTREAM_VERSION" ]; then
            show_upgrade_notes "$LOCAL_VERSION" "$UPSTREAM_VERSION"
        fi

        show_files_to_modify
        detect_local_modifications
        show_upstream_changes

        if ! has_changes && [ "$LOCAL_VERSION" = "$UPSTREAM_VERSION" ]; then
            echo ""
            echo -e "${GREEN}Everything is up to date!${NC}"
        fi

        exit 0
    fi

    # Normal mode: apply changes with confirmation
    if ! has_changes; then
        echo ""
        echo -e "${GREEN}Everything is up to date!${NC}"
        exit 0
    fi

    show_diffs
    show_summary

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
