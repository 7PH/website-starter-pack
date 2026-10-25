// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
//
// 301 /about/ -> /about, so a CMS page has one address for visitors and search
// engines. Registered by nuxt.config.ts only when CMS_ENABLED, hence outside
// server/middleware/.
import { getRouteRulesForPath } from 'nitropack/runtime/internal/route-rules';

export default defineEventHandler((event) => {
    const [path = '', query] = event.path.split(/\?(.*)/s);
    // /_nuxt/, /__sitemap__/...: framework paths, never CMS pages (slugs have no underscore).
    if (path === '/' || !path.endsWith('/') || path.startsWith('/_')) return;
    // Leading slashes collapsed too: "//evil.com/" or "/\evil.com/" must not redirect to another site.
    const target = `/${path.replace(/^[/\\]+|\/+$/g, '')}`;
    // A route rule redirecting the target (eg back to the slash) would loop.
    if (getRouteRulesForPath(target).redirect) return;
    return sendRedirect(event, query === undefined ? target : `${target}?${query}`, 301);
});
