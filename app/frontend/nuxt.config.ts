// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite';
import { SECURITY_HEADERS_OVERRIDE } from './config/security-headers';
import sitemapExt from './config/sitemap-ext';

const PUBLIC_URL = process.env.PUBLIC_URL || '';

// When MOBILE_APP=1, build a static SPA bundle suitable for bundling into a Capacitor wrapper.
const IS_MOBILE_APP = process.env.MOBILE_APP === '1';

// When SITEMAP_ENABLED=false, the @nuxtjs/sitemap module registers no /sitemap.xml
// route. High-scale apps (precomputed XML, cron-driven indexing) can flip this off
// and serve /sitemap.xml their own way — via public/, a server route, or upstream Nginx.
const SITEMAP_ENABLED = process.env.SITEMAP_ENABLED !== 'false';

// Default security headers (merged with project overrides)
const DEFAULT_SECURITY_HEADERS: Record<string, string> = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
};

// Merge and filter out empty values (empty string = remove header)
const securityHeaders = Object.fromEntries(
    Object.entries({ ...DEFAULT_SECURITY_HEADERS, ...SECURITY_HEADERS_OVERRIDE }).filter(([, value]) => value !== ''),
);

export default defineNuxtConfig({
    compatibilityDate: '2025-01-01',

    ...(IS_MOBILE_APP && {
        ssr: false,
        nitro: { preset: 'static' },
    }),

    // Route-specific rules
    routeRules: {
        // Security headers for all routes (customize in config/security-headers.ts)
        '/**': { headers: securityHeaders },
        // Disable SSR for auth/admin pages (auth is client-side, no SEO needed)
        '/admin/**': { ssr: false },
        '/login': { ssr: false },
        '/verify-email': { ssr: false },
        '/reset-password': { ssr: false },
    },

    app: {
        head: {
            title: process.env.NUXT_PUBLIC_APP_NAME || 'My App',
        },
        pageTransition: { name: 'page', mode: 'out-in' },
    },

    // Vite config for Docker/WSL2 file watching
    vite: {
        plugins: [tailwindcss()],
        server: {
            watch: {
                usePolling: true,
                interval: 1000,
            },
        },
    },

    runtimeConfig: {
        // Server-only (NOT exposed to the browser). Used by useApi during SSR
        // to reach the backend over the Docker network rather than the public URL.
        apiInternal: '', // NUXT_API_INTERNAL — e.g. http://backend:80/v1
        public: {
            appName: 'My App', // NUXT_PUBLIC_APP_NAME
            apiBase: '/api/v1', // NUXT_PUBLIC_API_BASE - relative path, same origin
            baseUrl: PUBLIC_URL, // Reuses existing PUBLIC_URL — used for sitemap, canonical, schema.org absolute URLs
            stripeEnabled: false, // NUXT_PUBLIC_STRIPE_ENABLED - enable billing features
            organizationsEnabled: false, // NUXT_PUBLIC_ORGANIZATIONS_ENABLED - enable org features
            managedAccountsEnabled: false, // NUXT_PUBLIC_MANAGED_ACCOUNTS_ENABLED - enable managed-account groups (email-less code sign-in)
            orgSelfServiceSubscriptions: true, // NUXT_PUBLIC_ORG_SELF_SERVICE_SUBSCRIPTIONS - allow org admins to subscribe
            orgSelfServiceCreation: true, // NUXT_PUBLIC_ORG_SELF_SERVICE_CREATION - allow users to create orgs
            orgInvitationsEnabled: false, // NUXT_PUBLIC_ORG_INVITATIONS_ENABLED - use email invitations instead of direct-add
            adminerUrl: '', // NUXT_PUBLIC_ADMINER_URL - external URL to Adminer
            // Umami Analytics (optional)
            umamiEnabled: false, // NUXT_PUBLIC_UMAMI_ENABLED
            umamiUrl: '', // NUXT_PUBLIC_UMAMI_URL
            umamiWebsiteId: '', // NUXT_PUBLIC_UMAMI_WEBSITE_ID
            umamiDashboardUrl: '', // NUXT_PUBLIC_UMAMI_DASHBOARD_URL - admin panel link
            defaultLocale: '', // NUXT_PUBLIC_DEFAULT_LOCALE
            mobileApp: IS_MOBILE_APP, // true when bundled inside a Capacitor wrapper
        },
    },

    modules: ['@pinia/nuxt', '@nuxt/ui', '@nuxtjs/i18n', '@vueuse/nuxt', '@nuxtjs/sitemap'],

    site: {
        url: PUBLIC_URL,
        name: process.env.NUXT_PUBLIC_APP_NAME || 'My App',
    },

    sitemap: {
        enabled: SITEMAP_ENABLED,
        // Disable auto-discovery; ship explicit URLs so private pages don't leak.
        // Sub-apps add their own public URLs via config/sitemap-ext.ts.
        excludeAppSources: true,
        urls: async () => {
            const defaults = [
                { loc: '/' },
                { loc: '/legal/privacy' },
                { loc: '/legal/terms' },
                { loc: '/legal/cookies' },
            ];
            const extra = await sitemapExt();
            return [...defaults, ...extra];
        },
    },

    colorMode: {
        preference: 'system',
        fallback: 'light',
        classSuffix: '',
        storageKey: 'color-mode',
    },

    icon: {
        // Use Iconify CDN to avoid /api conflict with backend proxy
        provider: 'iconify',
        serverBundle: 'remote',
        clientBundle: {
            scan: true,
        },
    },

    i18n: {
        // baseUrl + per-locale `language` enable hreflang emission. Currently a no-op
        // because strategy='no_prefix' means both locales share the same URL. To
        // ship translated content with proper hreflang, switch strategy to
        // 'prefix_except_default' (or similar) so each locale has a distinct URL.
        baseUrl: PUBLIC_URL,
        locales: [
            { code: 'fr', name: 'Français', language: 'fr-FR' },
            { code: 'en', name: 'English', language: 'en-US' },
        ],
        defaultLocale: (process.env.NUXT_PUBLIC_DEFAULT_LOCALE || 'en') as 'fr' | 'en',
        strategy: 'no_prefix',
        vueI18n: '~/config/i18n.ts',
        detectBrowserLanguage: {
            useCookie: true,
            cookieKey: 'i18n_locale',
            redirectOn: 'root',
        },
    },

    css: ['~/assets/css/main.css'],
});
