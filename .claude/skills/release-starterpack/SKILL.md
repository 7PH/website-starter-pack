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

5. Stamp `vNEXT` migrations with the target version. New migrations are authored
   as `YYYY-MM-DD-vNEXT-description.sql`; replace `vNEXT` with `vX.Y.Z` and update
   the manifest entries to match:
   ```bash
   VERSION=X.Y.Z  # set to the actual release version
   for f in app/backend/migrations/*-vNEXT-*.sql; do
       [ -f "$f" ] || continue
       new="${f/-vNEXT-/-v${VERSION}-}"
       git mv "$f" "$new"
       sed -i "s|^${f}\$|${new}|" starter-pack-files.txt
   done

   # Safety check: fail loudly if any vNEXT file slipped through
   if ls app/backend/migrations/*-vNEXT-*.sql 2>/dev/null | grep -q .; then
       echo "ERROR: vNEXT migrations remain after rename" && exit 1
   fi

   git add starter-pack-files.txt
   ```

6. Bump the version:
   ```bash
   # Edit .starterpack-version
   echo "X.Y.Z" > .starterpack-version
   ```

7. The new upgrade doc is auto-covered by `docs/upgrades/*` in `starter-pack-files.txt`.
   No manifest change needed unless adding a new skill or script.

8. Commit, push, and tag. The tag is load-bearing: `scripts/_core/core-update.sh`
   resolves the upgrade target from remote tags, so sub-apps cannot upgrade to
   this version until the tag is pushed.
   ```bash
   git add docs/upgrades/vX.Y.Z.md .starterpack-version <any other changed files>
   git commit -m "Release vX.Y.Z"
   git push
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

9. Ask the user to confirm before creating the GitHub release. Then:
   - Go to the repository's Releases page on GitHub
   - Click "Draft a new release"
   - Select the existing tag `vX.Y.Z` (created in step 8)
   - Set the title to `vX.Y.Z`
   - Copy the content of `docs/upgrades/vX.Y.Z.md` (minus the core header) as the release notes
   - Publish the release
