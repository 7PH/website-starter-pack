# Website Starter Pack

Full-stack web app template: Nuxt 3 frontend + FastAPI backend + PostgreSQL + Traefik reverse proxy.

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

## Theming & Dark Mode

The app uses **Tailwind CSS** for custom styling and **PrimeVue** for UI components. Both support dark mode via the `.dark` class.

### Styling Rules

1. **PrimeVue components** (Button, Card, DataTable, etc.): Use as-is, they handle dark mode automatically
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

### Don't Use

- PrimeVue CSS variables (`--p-*`) with `@apply` in scoped styles (doesn't work)
- `:global(.dark)` selectors (fragile, hard to maintain)

## Core Updates

```bash
bash scripts/_core/core-update.sh  # Sync files from starterpack repo
```

Requires clean git state. Uses `starter-pack-files.txt` manifest to pull files from `starter-pack` remote.
