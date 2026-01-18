<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

# Website Starter Pack

Full-stack web app template: Nuxt 3 frontend + FastAPI backend + PostgreSQL + Traefik reverse proxy.

## Before Claiming Done

**Always validate your changes before saying you're done.** Run the relevant checks:

```bash
# Code quality (no containers needed)
npm run lint:frontend                    # ESLint
npm run lint:backend                     # Ruff
npm run typecheck:frontend               # TypeScript

# Tests (no containers needed)
npm run test:unit:backend                # pytest
npm run test:unit:frontend               # vitest

# If modifying core files
bash scripts/_core/validate-core-files.sh

# If modifying dependencies or Dockerfile
npm run build                            # Rebuild containers
```

Fix any errors before claiming the task is complete.

## Quick Commands

```bash
npm run dev               # Start development
npm run stop              # Stop containers
npm run build             # Rebuild containers
npm run debug             # Dev with debugpy (port 5679)
npm run logs              # View logs
npm run lint:frontend     # Lint frontend (ESLint)
npm run lint:backend      # Lint backend (Ruff)
npm run typecheck:frontend # Typecheck frontend (Vue/TS)
```

## Stack

- **Frontend**: Nuxt 3, Pinia, @nuxt/ui, @nuxtjs/i18n
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL 15
- **Proxy**: Traefik (handles TLS, routing)
- **Analytics**: Umami (self-hosted)

## Key Concepts

### Starterpack Core Files
Files with the header `⚠️ STARTERPACK CORE — DO NOT MODIFY` are synced from the starterpack repo. Do not modify these files directly.

- **Manifest**: `starter-pack-files.txt` lists all synced files
- **Sync script**: `bash scripts/_core/core-update.sh` pulls latest from starterpack
- **Shell scripts**: All scripts in `scripts/_core/` are core files

Project-specific code lives alongside core files (same directories, different files).

### Component Overrides

Sub-apps can replace core components via `config/component-overrides.ts`:

```ts
export const componentOverrides = {
    OrganizationsCreateModal: () => import('~/components/custom/MyModal.vue'),
};
```

Override components must match the original's props/events contract. To add new override points, use `useOverridable()` in core components.

### URL Routing
- `/` - Frontend (Nuxt)
- `/api/*` - Backend API (prefix stripped by Traefik)
- Subdomains: `static.*`, `adminer.*`, `analytics.*`

### Database Migrations
Manual SQL files in `app/backend/migrations/`. Use `IF NOT EXISTS` for idempotency. Indexes should be defined in both SQLAlchemy models (for fresh installs) and migration files (for existing databases).

## Key Environment Variables

| Variable | Description |
|----------|-------------|
| `COMPOSE_PROJECT_NAME` | Docker container prefix |
| `PUBLIC_WEBSITE_HOST` | Domain for routing |
| `USE_TLS` | Enable HTTPS |
| `APP_DB_*` | PostgreSQL credentials |

## Development Tips

```bash
npm run build && npm run dev  # After requirements.txt changes
npm run db-connect            # Connect to database
npm run db-dump / db-restore  # Backup/restore database
```

## Testing Strategy

### Philosophy

- **Unit tests**: Only for complex functions with non-trivial logic (algorithms, data transformations, validation)
- **E2E tests**: For high-value, user-centric workflows (auth, payments, critical paths)
- Don't test simple CRUD or framework boilerplate—rely on types + linting

### Quick Commands

```bash
npm run test:unit:backend   # Run backend unit tests (pytest)
npm run test:unit:frontend  # Run frontend unit tests (vitest)
npm run test:e2e:start      # Start E2E test environment
npm run test:e2e            # Run E2E tests (Playwright)
npm run test:e2e:stop       # Stop E2E test environment
```

### Test Locations

| Type | Framework | Location |
|------|-----------|----------|
| Backend unit | pytest | `app/backend/tests/` |
| Frontend unit | Vitest | `app/frontend/tests/` |
| E2E | Playwright | `app/frontend/e2e/` |

### When to Write Tests

| Scenario | Test Type |
|----------|-----------|
| Complex algorithm/business logic | Unit test |
| Data transformation functions | Unit test |
| Input validation/sanitization | Unit test |
| User authentication flow | E2E test |
| Payment/checkout flow | E2E test |
| Critical user journeys | E2E test |
| Simple CRUD endpoint | Skip (types + linting) |
| UI component rendering | Skip (manual testing) |

## Theming & Dark Mode

The app uses **Tailwind CSS** for custom styling and **@nuxt/ui** for UI components. Both support dark mode via the `.dark` class.

### Styling Rules

1. **@nuxt/ui components** (UButton, UInput, UModal, etc.): Use as-is, they handle dark mode automatically
2. **Custom styling**: Use Tailwind utilities with `dark:` variants
3. **Colors**:
   - `primary-*` for brand/accent colors (defined in `tailwind.config.ts`)
   - `gray-*` for neutral backgrounds and text
   - `red-*`, `green-*`, `amber-*` for semantic colors

### Examples

```vue
<!-- Good: Tailwind dark mode classes -->
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">

<!-- Good: Scoped style with @apply -->
<style scoped>
.my-card {
    @apply bg-white dark:bg-gray-800 rounded-lg p-4;
}
</style>
```

### CSS Guidelines

- **Keep `main.css` minimal**: Only theme variables, CSS reset, and truly global utilities (like `.text-gradient-brand`)
- **No shared utility classes in main.css**: If multiple components need the same styling pattern, create a Vue component in `components/ui/` instead
- **Use scoped styles**: Component-specific CSS should be in `<style scoped>` blocks
- **Shared UI components** (`components/ui/`):
  - `CardHeader.vue` - card header with title and actions slot
  - `ModalHeader.vue` - modal header with title and close button
  - `FormActions.vue` - form action buttons container

## Type Generation (Backend → Frontend)

TypeScript types are auto-generated from Pydantic schemas. Don't manually define interfaces that mirror backend models.

```bash
./scripts/_core/convert-models.sh  # Regenerate after schema changes
```

- Schemas: `app/backend/src/schemas/`
- Register in: `app/backend/src/convert-models.py`
- Output: `app/frontend/types/models.ts`

## Core Updates

```bash
bash scripts/_core/core-update.sh  # Sync files from starterpack repo
```

Requires clean git state. Uses `starter-pack-files.txt` manifest to pull files from `starter-pack` remote.

## Internationalization (i18n)

### Admin Pages

Admin pages (`/admin/*`) are **English-only** and do not require i18n translations. These pages are intended for internal use by developers and system administrators who are expected to understand English.

When working on admin pages:
- Use hardcoded English strings directly
- Do not add translation keys to locale files
- Keep UI text simple and technical

### User-Facing Pages

All other pages that end users interact with must use i18n:
- Use `t('key')` for all user-visible text
- Add translation keys to `locales/core-en.json` and `locales/core-fr.json`
- Follow existing naming conventions for translation keys
