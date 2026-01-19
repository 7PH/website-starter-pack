<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

# Upgrade Notes

This directory contains upgrade notes for each version of the starterpack. These notes are designed to help AI assistants (and humans) understand what changed between versions and how to safely upgrade.

## File Format

Each version has a corresponding `vX.Y.Z.md` file with the following structure:

```markdown
# Starterpack vX.Y.Z

**Release Date:** YYYY-MM-DD
**Type:** Major | Minor | Patch

## Breaking Changes

### BC-001: Short descriptive title
**Severity:** HIGH | MEDIUM | LOW
**Affected files:** `path/to/file.py`, `another/file.ts`

Description of what changed and why it matters.

**Required action:**
1. Step one to resolve
2. Step two to resolve

## New Features

### FEAT-001: Feature name
**Files:** `new/file.ts`

Description of the new feature and how to use it.

## Migrations Required

List any SQL migrations that need to be run:
- `app/backend/migrations/YYYY-MM-DD-description.sql` - What it does

## Deprecations

List any deprecated features that will be removed in future versions.
```

## Version Types

- **Major** (X.0.0): Breaking changes that require manual intervention
- **Minor** (0.X.0): New features, backward-compatible changes
- **Patch** (0.0.X): Bug fixes, documentation updates

## Severity Levels

- **HIGH**: Application will not work without action
- **MEDIUM**: Some features may not work correctly
- **LOW**: Cosmetic or minor behavioral changes

## Writing Good Upgrade Notes

1. **Be specific**: Include exact file paths and code changes
2. **Explain why**: Help readers understand the reasoning
3. **Provide solutions**: Every breaking change should have clear resolution steps
4. **Test your notes**: Verify the upgrade path works as documented
