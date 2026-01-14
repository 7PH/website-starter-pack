/**
 * Project-specific security headers overrides for Nuxt.
 *
 * Customize security headers by modifying SECURITY_HEADERS_OVERRIDE below.
 * These values will be merged with the defaults in nuxt.config.ts.
 *
 * Set a header to empty string "" to remove it.
 */

export const SECURITY_HEADERS_OVERRIDE: Record<string, string> = {
    // Examples:
    // "X-Frame-Options": "",  // Empty string removes the header (allow iframes)
    // "X-Frame-Options": "DENY",  // Override default value
    // "Cross-Origin-Resource-Policy": "cross-origin",  // Add new header
};
