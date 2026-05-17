<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

# vNEXT

- **Released:** vNEXT
- **Summary:** CI rebuild. Halved the number of workflow jobs by consolidating frontend checks (lint + typecheck + vitest) and backend checks (ruff + pytest) into single jobs that share one install. Every workflow now uses GHA Docker layer cache, cancels superseded PR runs, and reads `runs-on` from an optional `CI_RUNNER_LABEL` repo variable so sub-apps with a self-hosted runner can route all CI off paid GitHub minutes. `Build (prod)` now skips on PRs when preview is enabled (preview already builds+deploys prod images, strictly stronger verification). `Models Sync` gates on a tiny changes-detection job so it skips when no Pydantic-affecting files changed. No coverage lost — same checks, just cheaper.

## Upgrade Notes

**Non-breaking by default.** Sub-apps that don't set `CI_RUNNER_LABEL` keep using `ubuntu-latest` exactly as today; the only visible change is the GitHub Actions UI now shows two grouped checks (`Frontend Checks`, `Backend Checks`) instead of five (`Lint`, `Type Check`, `Unit Tests`, each with frontend/backend halves).

`/upgrade-starterpack` removes the old workflow files for you (`lint.yml`, `typecheck.yml`, `unit-tests.yml`) because `core-update.sh` deletes core files no longer present in `starter-pack-files.txt`. If your sub-app has branch protection rules pinned to the old check names (e.g. "Frontend (ESLint)"), update them to `Lint + Typecheck + Vitest` and `Ruff + Pytest` after the upgrade or PRs won't be mergeable.

### Optional: route CI to a self-hosted runner

If you have a self-hosted runner, set the `CI_RUNNER_LABEL` repo variable to its custom label:

```
gh variable set CI_RUNNER_LABEL --body "preview-host"   # or whatever your runner label is
```

Every workflow except `preview.yml` then resolves `runs-on` to `[self-hosted, <your-label>]`. The `self-hosted` part is added automatically — you only set your custom label. Unset the variable to fall back to `ubuntu-latest`.

Preview still uses its dedicated `[self-hosted, preview-host]` label combo regardless of `CI_RUNNER_LABEL`, because it's tied to the preview networking stack (its own runner, its own infra).

**Debug tip:** if jobs sit in "Waiting for runner" after setting the variable, the label probably doesn't match any online runner. Check `Settings → Actions → Runners` for active labels. Unset the variable to fall back to `ubuntu-latest`.

### Migration

None.

## Changed Core Files

- `.github/workflows/build.yml` — Docker BuildKit GHA cache (per-image scope), `CI_RUNNER_LABEL` fallback, PR-only `cancel-in-progress`, 30 min timeout, job-level `if:` to skip on same-repo PRs when `PREVIEW_BASE_DOMAIN` is set.
- `.github/workflows/e2e.yml` — Same Docker cache pattern, Playwright browser cache keyed on `package-lock.json`, `CI_RUNNER_LABEL` fallback, PR-only cancel, 30 min timeout.
- `.github/workflows/models-sync.yml` — `CI_RUNNER_LABEL` fallback, PR-only cancel, 15 min timeout, shared `backend-dev` GHA cache scope with `e2e.yml`, gating `changes` job that diffs the PR and skips the expensive sync check when no Pydantic-affecting files changed.
- `.github/workflows/validate-core.yml` — `CI_RUNNER_LABEL` fallback, PR-only cancel, 15 min timeout.

## New Core Files

- `.github/workflows/checks-frontend.yml` — One job: `npm ci` once, then `lint + typecheck + vitest` with `continue-on-error: true` per step and a final fail-if-any aggregator so all errors surface in one run.
- `.github/workflows/checks-backend.yml` — One job: `pip install -r requirements.txt` once (pip cache), then `ruff + pytest` with the same continue-then-aggregate pattern.

## Removed Core Files

- `.github/workflows/lint.yml` — merged into `checks-frontend.yml` + `checks-backend.yml`.
- `.github/workflows/typecheck.yml` — merged into `checks-frontend.yml`.
- `.github/workflows/unit-tests.yml` — merged into `checks-frontend.yml` + `checks-backend.yml`.

## New Features

### `CI_RUNNER_LABEL` repo variable

Optional GitHub Actions repo variable. When set, every workflow except `preview.yml` runs on a runner with that label instead of `ubuntu-latest`. Unset → existing behavior. No code change in sub-apps required to adopt or revert.

### GHA Docker layer cache

`build.yml` and `e2e.yml` now use `docker/setup-buildx-action@v3` and write a `docker-bake.override.hcl` that maps each known core build target to its own GHA cache scope. Combined with `COMPOSE_BAKE=true`, `docker compose build` delegates to `buildx bake` and respects the cache config.

Sub-apps that add their own services to a prod profile don't break — they just build without cache for the new services unless they extend the workflow. Hit the cache by extending `docker-bake.override.hcl` with a target block for each app-specific build.

### Concurrency cancel-in-progress (PR only)

Each workflow groups by `${{ github.workflow }}-${{ github.ref }}` and cancels superseded runs **only when the trigger is `pull_request`**. Master-push runs always complete so direct-to-master releases never lose validation mid-flight.
