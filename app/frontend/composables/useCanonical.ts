// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Emit a `<link rel="canonical">` tag for the current page (or a custom URL).
 *
 * Default behavior: with no argument, uses the current route's `path` (query
 * strings dropped) resolved against `useRuntimeConfig().public.baseUrl`. Pass
 * a path or absolute URL to override.
 *
 * @example
 * useCanonical();                           // <link rel="canonical" href="https://example.com/current/path">
 * useCanonical('/canonical/path');          // resolved against baseUrl
 * useCanonical('https://example.com/abs');  // used as-is
 */
export function useCanonical(pathOrUrl?: string) {
    const baseUrl = useRuntimeConfig().public.baseUrl;
    const route = useRoute();
    const href = buildCanonicalUrl(pathOrUrl ?? route.path, baseUrl);
    useHead({ link: [{ rel: 'canonical', href, key: 'canonical' }] });
}

/**
 * Build a canonical URL string. Absolute URLs are returned unchanged; relative
 * paths get their query string stripped and are joined to `baseUrl`.
 */
export function buildCanonicalUrl(pathOrUrl: string, baseUrl: string): string {
    if (/^https?:\/\//.test(pathOrUrl)) {
        return pathOrUrl;
    }
    const trimmedBase = baseUrl.replace(/\/$/, '');
    const pathOnly = pathOrUrl.split('?')[0] ?? pathOrUrl;
    const prefix = pathOnly.startsWith('/') ? '' : '/';
    return `${trimmedBase}${prefix}${pathOnly}`;
}
