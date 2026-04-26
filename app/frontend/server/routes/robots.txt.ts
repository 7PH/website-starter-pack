// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Dynamic /robots.txt route.
 *
 * Defaults: Disallow /admin and /api. The Sitemap line points at
 * /sitemap.xml on the configured baseUrl.
 *
 * Sub-apps add extra Disallow paths via `config/robots-ext.ts`.
 *
 * Note: `public/robots.txt` must NOT exist — Nuxt serves files in `public/`
 * before nitro routes get a chance to handle the request.
 */

import robotsExt from '~/config/robots-ext';

export default defineEventHandler(async (event) => {
    const baseUrl = useRuntimeConfig(event).public.baseUrl;
    const extra = (await robotsExt()) ?? [];
    const lines = [
        'User-agent: *',
        'Disallow: /admin',
        'Disallow: /api',
        ...extra.map((rule) => `Disallow: ${rule}`),
        '',
        `Sitemap: ${baseUrl}/sitemap.xml`,
    ];
    setHeader(event, 'content-type', 'text/plain');
    return lines.join('\n');
});
