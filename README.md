# website-starter-pack

## Install

Ensure you have `git` and `docker` on your machine, then:

- Ensure you are running as a non-root user (highly recommended)
- Clone the repository
- Execute `npm run setup`
- Fill the `.env` file

## Running

For running in production, run `npm start`

For usual development (Nuxt debugger, frontend and backend hot-reload):

- Run `npm run dev`

For debugging the python process inside the backend container:

- Ensure you are using VSCode
- Run `npm run debug`
- In the VSCode Debugger Tab, execute the action `Debug Backend`

## Database

### Backup

To backup the database:

- Run `npm run db-dump`
- Verify the generated SQL file in `backups/`

To restore a backup:

- Delete database data folder with `sudo rm -rf services/db/data/ && npm run setup` (⚠️)
- Run `npm run db-restore -- backups/<path-to-the-sql-dump>.sql.gz`

### Initial state

To ensure new databases automatically start from a specific backup:

- Delete database data folder with `sudo rm -rf services/db/data/ && npm run setup` (⚠️)
- Move the backup from `backups/*.sql.gz` to `services/db/initdb.sql`

Beware that `initdb.sql` is tracked by Git.
