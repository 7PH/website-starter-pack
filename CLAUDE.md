# Website Starter Pack

Full-stack web app template: Nuxt 3 frontend + FastAPI backend + PostgreSQL + Traefik reverse proxy.

## Quick Commands

```bash
npm run dev      # Start development
npm run stop     # Stop containers
npm run build    # Rebuild containers
npm run debug    # Dev with debugpy (port 5679)
npm run logs     # View logs
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
Manual SQL files in `app/backend/migrations/`. Use `IF NOT EXISTS` for idempotency. SQLAlchemy handles table creation; migrations handle indexes, alterations, etc.

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

## Core Updates

```bash
bash scripts/_core/core-update.sh  # Sync files from starterpack repo
```

Requires clean git state. Uses `starter-pack-files.txt` manifest to pull files from `starter-pack` remote.
