<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

# Website Starter Pack

Full-stack web app template: Nuxt 3 frontend + FastAPI backend + PostgreSQL + Traefik reverse proxy.

## Validation (Before Claiming Done)

```bash
npm run lint:frontend && npm run lint:backend && npm run typecheck:frontend
npm run test:unit:backend && npm run test:unit:frontend
bash scripts/_core/validate-core-files.sh  # If modifying core files
npm run build                               # If modifying dependencies/Dockerfile
```

## Quick Commands

```bash
npm run dev      # Start development
npm run stop     # Stop containers
npm run build    # Rebuild containers
npm run logs     # View logs
```

## Stack

- **Frontend**: Nuxt 3, Pinia, @nuxt/ui, @nuxtjs/i18n
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL 15
- **Proxy**: Traefik (handles TLS, routing)

## Key Concepts

### Core Files
Files with `⚠️ STARTERPACK CORE — DO NOT MODIFY` header are synced from starterpack. Don't modify directly.
- Manifest: `starter-pack-files.txt`
- Sync: `bash scripts/_core/core-update.sh`

### Component Overrides
Sub-apps can replace core components via `config/component-overrides.ts`. Override components must match original props/events. Use `useOverridable()` to add new override points.

### URL Routing
`/` → Frontend, `/api/*` → Backend (prefix stripped), Subdomains: `static.*`, `adminer.*`, `analytics.*`

### Migrations
Manual SQL in `app/backend/migrations/`. Use `IF NOT EXISTS`. Define indexes in both models and migrations.

## Testing

**Philosophy**: Unit tests for complex logic only. E2E for critical user flows. Skip simple CRUD (rely on types + linting).

- Backend: `app/backend/tests/` (pytest)
- Frontend: `app/frontend/tests/` (vitest)
- E2E: `app/frontend/e2e/` (Playwright)

## Styling

- **@nuxt/ui components**: Use as-is (dark mode automatic)
- **Custom styling**: Tailwind with `dark:` variants
- **Colors**: `primary-*` for brand, `gray-*` for neutrals, semantic colors for states
- **CSS**: Keep `main.css` minimal. Use `<style scoped>`. Create Vue components for shared patterns.

## Type Generation

Types auto-generated from Pydantic schemas. Run `./scripts/_core/convert-models.sh` after schema changes.

## i18n

- **Admin pages** (`/admin/*`): English-only, no translations needed
- **User-facing pages**: Use `t('key')`, add keys to `locales/core-en.json` and `locales/core-fr.json`

## Upgrades

1. Analyze: `bash scripts/_core/core-update.sh --analyze`
2. Execute: `bash scripts/_core/core-update.sh`
3. Re-apply local modifications if needed
4. Validate: `npm run lint:frontend && npm run typecheck:frontend`

See `docs/upgrades/` for version-specific notes.
