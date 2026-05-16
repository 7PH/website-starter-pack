import type { NitroConfig } from 'nitropack';

/**
 * Sub-app extension for nitro route rules.
 *
 * Use this for two main concerns:
 *
 *   1. Legacy URL redirects — preserve old paths after a rename so external
 *      links and SEO survive. nitro emits a real HTTP 301 (verified).
 *
 *   2. SSR caching — for pages whose render hits a slow DB query or expensive
 *      computation. nitro caches the rendered HTML server-side and emits
 *      `Cache-Control: s-maxage=<ttl>, stale-while-revalidate`. Measured on
 *      starter dev with a 400ms server-side setup: cold ~484ms, warm ~12ms
 *      (≈40× speedup, same TTL window). No additional cache-driver config
 *      needed — works out of the box.
 *
 * Starter's own routeRules (security headers, /admin SSR-off, etc.) take
 * precedence on conflict — sub-app overrides are silently dropped for those
 * keys. If you genuinely need to override a starter-shipped rule, that's a
 * conversation, not a fix you should ship in this file.
 *
 * @example
 * export const ROUTE_RULES_EXT = {
 *     // 301 a legacy URL to its current home
 *     '/old-pricing': { redirect: { to: '/pricing', statusCode: 301 } },
 *     // Cache a slow page for 1h, stale-while-revalidate
 *     '/media/**': { swr: 3600 },
 *     // Static page worth prerendering at build time
 *     '/about': { prerender: true },
 * } satisfies NitroConfig['routeRules'];
 */
export const ROUTE_RULES_EXT = {} satisfies NitroConfig['routeRules'];
