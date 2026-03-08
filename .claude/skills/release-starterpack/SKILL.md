<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
---
name: release-starterpack
description: Release a new starterpack version
---

# Release Starterpack

Steps to publish a new starterpack version.

## Steps

1. Read current version:
   ```bash
   cat .starterpack-version
   ```

2. Determine new version (patch/minor/major) based on changes:
   - **Patch** (x.y.Z): bug fixes only
   - **Minor** (x.Y.0): new features, no breaking changes
   - **Major** (X.0.0): breaking changes

3. Review commits since last release:
   ```bash
   git log --oneline
   ```

4. Create `docs/upgrades/vX.Y.Z.md` with the core header and sections:
   - Release date
   - Summary sentence
   - New Core Files (if any new files added to starterpack)
   - Bug Fixes (if any)
   - Upgrade Notes (breaking changes, migrations needed, or "No breaking changes")

   Show the draft to the user and ask for confirmation before continuing.

5. Bump the version:
   ```bash
   # Edit .starterpack-version
   echo "X.Y.Z" > .starterpack-version
   ```

6. The new upgrade doc is auto-covered by `docs/upgrades/*` in `starter-pack-files.txt`.
   No manifest change needed unless adding a new skill or script.

7. Commit and push:
   ```bash
   git add docs/upgrades/vX.Y.Z.md .starterpack-version <any other changed files>
   git commit -m "Release vX.Y.Z"
   git push
   ```

8. Ask the user to confirm before creating the GitHub release. Then:
   - Go to the repository's Releases page on GitHub
   - Click "Draft a new release"
   - Create a new tag `vX.Y.Z` targeting `master`
   - Set the title to `vX.Y.Z`
   - Copy the content of `docs/upgrades/vX.Y.Z.md` (minus the core header) as the release notes
   - Publish the release
