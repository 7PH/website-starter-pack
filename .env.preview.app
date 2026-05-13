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
#
# Roster of users to upsert into the preview DB after the stack is healthy.
# JSON array on a single line. Leave unset to inherit the core default
# (admin/user/premium under @preview.app — see scripts/_core/seed-preview-users.sh).
#
# Spec fields: email (required), password (required), is_admin, is_premium,
# first_name, last_name, display_name. Managed-account seeding isn't supported
# by /internal/seed-users yet; if you need it, create the group + accounts
# from a follow-up step using the managed-account-groups API.
#
#   PREVIEW_SEED_USERS=[{"email":"teacher@preview.app","password":"pw","is_premium":true},{"email":"student@preview.app","password":"pw"}]
