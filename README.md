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

## Database backup

To backup the database:

- Run `npm run db-dump`
- Verify the generated SQL file with `head -n 100 services/db/initdb.sql`

To restore a backup:

- Ensure your dump file is at `services/db/initdb.sql`
- Delete database data folder with `sudo rm -rf services/db/data/ && npm run setup` (⚠️)
- Re-run the database container
