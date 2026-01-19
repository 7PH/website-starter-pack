<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

# Upgrading the Starterpack

This guide explains how to upgrade your project to a newer version of the starterpack.

## Quick Start

### Option 1: AI-Assisted Upgrade (Recommended)

Use the `/upgrade-starterpack` slash command with Claude to get AI-assisted upgrade support:

1. Claude will analyze the upgrade and detect local modifications
2. Review the upgrade plan for breaking changes
3. Approve the plan to execute the upgrade
4. Claude will re-apply your local changes where appropriate

### Option 2: Manual Upgrade

1. Run upgrade analysis:
   ```bash
   bash scripts/_core/core-update.sh --analyze
   ```

2. Review the output for:
   - Version changes (current → target)
   - Breaking changes in upgrade notes
   - Local modifications that will be overwritten
   - Required migrations

3. Apply the upgrade:
   ```bash
   bash scripts/_core/core-update.sh
   ```

4. Run post-upgrade checks:
   ```bash
   npm run lint:frontend && npm run lint:backend
   npm run typecheck:frontend
   bash scripts/_core/validate-core-files.sh
   ```

## Understanding the Analysis Output

When you run `--analyze`, you'll see:

```
=== STARTERPACK UPGRADE ANALYSIS ===
Current version: 1.0.0
Target version: 1.1.0

=== UPGRADE NOTES ===
[Contents of applicable docs/upgrades/vX.Y.Z.md files]

=== FILES TO BE MODIFIED ===
[List of files that will change]

=== LOCAL MODIFICATIONS (will be overwritten) ===
[Diff showing your local changes to core files]

=== UPSTREAM CHANGES ===
[Diff showing what changed upstream]
```

## Handling Local Modifications

If you've modified core files (files with `⚠️ STARTERPACK CORE` header):

1. **Backup your changes**: The `--analyze` output shows the diff of your modifications
2. **Apply the upgrade**: Run `core-update.sh` to sync with upstream
3. **Re-apply your changes**: Manually or with AI assistance, merge your modifications back

**Best practice**: Avoid modifying core files directly. Use:
- Extension files (e.g., `main_ext.py`, `*-ext.ts`)
- Component overrides (`config/component-overrides.ts`)
- Separate project-specific files

## Version History

Detailed notes for each version are in `docs/upgrades/`:

| Version | Date | Type | Notes |
|---------|------|------|-------|
| v1.0.0 | 2026-01-19 | Major | Initial versioned release |

## Troubleshooting

### "Git working directory is not clean"

The upgrade script requires a clean git state. Commit or stash your changes first:
```bash
git stash
bash scripts/_core/core-update.sh
git stash pop
```

### Merge conflicts after upgrade

If you have local modifications that conflict with upstream changes:
1. Review both versions (your local + upstream)
2. Decide which changes to keep
3. Use the Edit tool or manual editing to merge

### Linting errors after upgrade

New versions may introduce stricter linting rules. Fix errors reported by:
```bash
npm run lint:frontend
npm run lint:backend
```

### Type errors after upgrade

Schema changes may require regenerating types:
```bash
./scripts/_core/convert-models.sh
```
