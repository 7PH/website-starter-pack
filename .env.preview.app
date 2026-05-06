# App-specific env vars for PR preview environments.
#
# Loaded by .github/workflows/preview.yml after .env.ci and before the
# per-PR heredoc, so values here override .env.ci defaults but cannot
# override preview infrastructure (COMPOSE_FILE, PUBLIC_PORT, host, etc.).
#
# NOT loaded by e2e tests — those stay on .env.ci alone, so anything
# you add here will not affect `npm run test:e2e`.
#
# Use cases: enable a paid integration with a preview-only key, flip an
# app-specific feature flag, set a custom default. This file is committed,
# so don't put production secrets here — use preview-only credentials.
#
# Examples:
#   LLM_ENABLED=true
#   LLM_API_KEY=sk-preview-...
#   MY_APP_FEATURE_X=enabled
