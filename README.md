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

## CMS mode (content sites)

For sites a non-technical client edits on their own (brochure sites, small businesses). Off by default.

1. Set `CMS_ENABLED=true` in `.env` and rebuild the frontend (the public page route is added at build time).
2. Declare your templates in `app/backend/src/cms_templates_ext.py` (see the example in that file).
3. In the admin user page, turn your client into a **CMS editor**. The editor then sees only **Pages** and **Photos** in the admin, plus an "Edit site" link in the user menu.

What you get:

- **Photos** (`/admin/cms/media`): upload (JPEG, PNG, WebP, 15 MB, 40 MP max), turned into WebP at 480/960/1600/2400 px, metadata stripped, with alt text and a focal point. Files live in `static/cms/media/<id>-<token>/` (the random token keeps photos of unpublished pages unguessable) and are served by the static host (override the origin with `STATIC_ORIGIN`).
- **Pages** (`/admin/cms/pages`):
  - **Fixed templates** (`fixed=True`, eg `home`, `site`) have one page each. Read them in your own pages with `useCmsFixed('home')`. Fields never filled return their `default`.
  - **Free templates** (core ships `default`: one rich text body) have any number of pages, served at `/<slug>` with SSR, SEO tags and sitemap entries. Your own routes always win over CMS slugs. If your app has its own top-level dynamic page (`pages/[slug].vue`, `pages/[...slug].vue`), the CMS route is not added (the build logs a warning): render CMS pages from it with `useCmsPage(slug)`. Addresses can't start with `api` (routed to the backend). `/about/` redirects to `/about`.
  - List the pages of one template in the order the editor sets (drag and drop in the pages list, arrows on touch screens) with `useCmsPageList('service')`, eg for a grid of services. For a blog, declare a `post` template and list it newest first with `useCmsPageList('post', { order: 'published_at' })`. Render rich text with `<CmsRichText :html>` and photos with `<CmsImage :media>`. Restyle free pages by overriding `CmsPageContent` in `config/component-overrides.ts`.
  - The editor has a Visual/HTML toggle and a live preview of unsaved changes. Addresses `admin*` and core routes are refused too, and the editor warns before saving an address a site route would hide (`legal`, because of `/legal/privacy`). A save is refused when the page changed since it was loaded (another tab, a quick edit), so nothing gets overwritten silently.
  - Import scripts can set `published_at` in the update payload to keep a post's original date.
- **Quick edit on the page itself**: wrap any part of your pages in `<CmsEditable :page="home" field="tagline">…</CmsEditable>`. People who can edit get a pencil opening a modal for that field, and the page data refreshes in place. For an empty field, pass `add-label="…"` and no content: editors get an add button, visitors nothing. Add `<CmsPageEditButton :page="home" />` for a shortcut to the full editor (free pages get it automatically). Edit controls are rendered in the browser only: visitors' HTML just gets a plain `<div>` around each wrapped part.
- **Backups** also archive `static/cms/` (`cms_media_<stamp>.tar`) next to each database dump, and restore both.
- `<html lang>` follows the site's language.
- **SEO on free pages**: `<title>` is "<SEO title> · <site name>" (`NUXT_PUBLIC_APP_NAME`), plus `og:site_name`, `og:locale` and JSON-LD (WebPage and a Home > page breadcrumb). Set `schema_type="Article"` on a template for dated content (eg `post`): its pages get Article JSON-LD with their dates and `og:type` article.
- **Local business**: call `useSchemaLocalBusiness({ type: 'HealthAndBeautyBusiness', name, url, telephone, address: { streetAddress, postalCode, addressLocality, addressCountry }, openingHours, sameAs })` on your home page, eg with the data of a fixed `site` page, so search engines get your address, phone and hours.

Adding a field to a template needs no migration. The `cms_*` tables are created in every app, even with the flag off (they stay empty).

## Running

For running in production, run `npm start`

Behind a reverse proxy (nginx, optionally Cloudflare)? Run `npm run setup-host-proxy` so the app records real client IPs instead of the Docker gateway. Topologies and manual steps: [docs/deployment/reverse-proxy.md](docs/deployment/reverse-proxy.md).

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
