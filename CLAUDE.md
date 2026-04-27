<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

# Website Starter Pack

Full-stack web app template: Nuxt 3 frontend + FastAPI backend + PostgreSQL + Traefik reverse proxy.

To check if you are in the starterpack or a sub-app, run `git remote get-url origin`.

## Validation (Before Claiming Done)

```bash
npm run lint:frontend && npm run lint:backend && npm run typecheck:frontend
npm run test:unit:backend && npm run test:unit:frontend
bash scripts/_core/validate-core-files.sh  # If modifying core files
npm run build                               # If modifying dependencies/Dockerfile
```

## Quick Commands

```bash
npm run dev      # Start development (hot reload, Traefik on :8080)
npm run start    # Start production (Nginx, TLS-ready)
npm run stop     # Stop all containers
npm run restart  # Stop + dev
npm run build    # Rebuild containers
npm run logs     # View logs
```

### E2E Testing

```bash
npm run test:e2e:start   # Spin up isolated test env on port 13001
npm run test:e2e         # Run Playwright tests
npm run test:e2e:stop    # Tear down test env
```

### Checking If Running

```bash
docker compose ps                                # List running containers
curl http://localhost/api/v1/healthcheck          # Backend health (dev)
curl http://localhost:13001/api/v1/healthcheck    # Backend health (e2e)
```

Traefik dashboard: `http://localhost:8080` (dev only).

## Stack

- **Frontend**: Nuxt 3, Pinia, @nuxt/ui, @nuxtjs/i18n
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL 15 (`npm run db-connect` for psql access)
- **Proxy**: Traefik (handles TLS, routing)
- **Env vars**: See `.env.template` for all available config

### Feature Flags

Toggle features via env vars: `STRIPE_ENABLED`, `ORGANIZATIONS_ENABLED`, `OAUTH_ENABLED`, `LLM_ENABLED`.

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
Manual SQL in `app/backend/migrations/`. Name new migrations `YYYY-MM-DD-vNEXT-description.sql` — the release skill rewrites `vNEXT` to the target version at release time. Use `IF NOT EXISTS`. Define indexes in both models and migrations.

## Testing

**Philosophy**: Unit tests for complex logic only. E2E for critical user flows. Skip simple CRUD (rely on types + linting).

- Backend: `app/backend/tests/` (pytest)
- Frontend: `app/frontend/tests/` (vitest)
- E2E: `app/frontend/e2e/` (Playwright)

## i18n

ALL user-facing text must be translated. Never hardcode user-visible strings.

- **Admin pages** (`/admin/*`): English-only, no translations needed
- **User-facing pages**: Use `const { t } = useI18n()` then `t('key')`
- **Locale files**: `locales/core-{en,fr}.json` (starterpack-managed) + `locales/{en,fr}.json` (app-specific, deep merged)
- **Locale switching**: `useAppLocale()` composable

## Styling

- **@nuxt/ui components**: Use as-is (dark mode automatic)
- **Custom styling**: Tailwind with `dark:` variants
- **Colors**: `primary-*` for brand, `gray-*` for neutrals, semantic colors for states
- **Inline utilities first**: write Tailwind classes directly on the element. Don't reach for `<style scoped>` + `@apply` for one-off styling — it adds a name-to-rule indirection that obscures the actual CSS and breaks Tailwind IntelliSense.
- **`<style scoped>` is for what utilities can't express**: `:hover`/`:focus`-within compounds, animations/keyframes, or a class repeated 3+ times in the same file (extracting it then beats DRY violations).
- **Avoid `:deep()`**: it pierces component encapsulation and breaks when the child's markup changes between versions. Use the component's documented styling API instead — for Nuxt UI, that's the `:ui` prop with slot keys (`:ui="{ base: 'font-mono text-center' }"`), or class-forwarding props the component exposes. If a child component genuinely doesn't surface what you need, extract that styling concern into a wrapper component or file an issue against the library.
- **Repeated patterns** across files: pull them into a small Vue component, not a shared CSS class. Components compose; classes don't.
- **`main.css` stays minimal**: theme tokens, page layout primitives (`page-box`, `page-content-width`), and that's it. No utility-shorthand classes.

## Premium gating

Frontend `<PremiumGate>` (with `#teaser` / `#gated` slots) is UX, not security. Real entitlement is server-side: every premium write endpoint must depend on `require_premium`. Apps own this helper — pattern mirrors `get_current_admin` in `app/backend/src/helpers/auth.py`. Resolve effective premium via `is_premium_effective(session, db_user)` so managed accounts inherit from their group owner:

```python
async def require_premium(
    session: Session = Depends(get_session),
    user: UserRead = Depends(get_current_user),
) -> UserRead:
    db_user = get_user_by_id(session, user.id)
    if not db_user or not is_premium_effective(session, db_user):
        raise HTTPException(status_code=402, detail="Premium required")
    return user
```

Use `usePremiumStatus()` for entitlement reads outside markup; use `<PremiumBadge>` to mark premium content visually.

## Type Generation

Types auto-generated from Pydantic schemas. Run `./scripts/_core/convert-models.sh` after schema changes.

## Upgrades

Use `/upgrade-starterpack`. See `docs/upgrades/` for version-specific notes.

## App-Specific Instructions

@CLAUDE.app.md
