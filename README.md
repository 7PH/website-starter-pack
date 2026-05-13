# website-starter-pack

## Install

Ensure you have `git` and `docker` on your machine, then:

- Ensure you are running as a non-root user (highly recommended)
- Clone the repository
- Execute `npm run setup`
- Fill the `.env` file

## OAuth (Google Sign-In)

To enable "Continue with Google" on the login page:

1. **Create OAuth credentials** in [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Add authorized redirect URIs:
     - Production: `https://YOUR_DOMAIN/oauth/callback`
     - Local dev: `http://localhost:3000/oauth/callback` (Google only allows plain `localhost`, not custom `.localhost` domains)

2. **Configure environment variables** in `.env`:
   ```
   OAUTH_ENABLED=true
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

The Google sign-in button will appear on the login and signup pages when properly configured.

## Mobile wrapper (Capacitor)

The starterpack is Capacitor-ready: outbound URLs (Stripe checkout / billing portal, Google OAuth) route through `useNativeBridge()`. On the web it's a no-op stub; in a Capacitor wrapper, install a real bridge from a client plugin:

```ts
// app/frontend/plugins/capacitor.client.ts (app-owned, not core)
import { Browser } from '@capacitor/browser';
import type { NativeBridge } from '~/composables/useNativeBridge';

export default defineNuxtPlugin(() => {
    window.__nativeBridge = {
        isNative: () => true,
        openExternal: (url) => Browser.open({ url }).then(() => undefined),
    } satisfies NativeBridge;
});
```

**Build:** `MOBILE_APP=1 npm run build` (inside `app/frontend/`) produces a static SPA in `.output/public/` for bundling into the wrapper.

**OAuth deep-link:** the wrapper listens on `App.appUrlOpen`, parses the callback URL, and navigates the webview to `/oauth/callback?code=...&state=...`. The existing route's `handleOAuthCallback` does the rest.

**Extending the bridge** with app-specific methods (haptic, audio, push) — use TypeScript module augmentation:

```ts
// In your app's plugin file or a dedicated `types/native-bridge.d.ts`:
declare module '~/composables/useNativeBridge' {
    interface NativeBridge {
        haptic(): Promise<void>;
        playSample(note: string): Promise<void>;
    }
}
```

Methods added this way are typed everywhere `useNativeBridge()` is called. Core does not call them — only app code does.

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
