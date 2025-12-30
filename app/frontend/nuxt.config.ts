// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite';

export default defineNuxtConfig({
    compatibilityDate: '2025-01-01',

    // Disable SSR for admin pages (auth is client-side, no SEO needed)
    routeRules: {
        '/admin/**': { ssr: false },
    },

    app: {
        head: {
            title: process.env.NUXT_PUBLIC_APP_NAME || 'My App',
        },
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
        public: {
            appName: 'My App', // NUXT_PUBLIC_APP_NAME
            apiBase: '/api', // NUXT_PUBLIC_API_BASE - relative path, same origin
            // Umami Analytics (optional)
            umamiEnabled: false, // NUXT_PUBLIC_UMAMI_ENABLED
            umamiUrl: '', // NUXT_PUBLIC_UMAMI_URL
            umamiWebsiteId: '', // NUXT_PUBLIC_UMAMI_WEBSITE_ID
        },
    },

    modules: ['@pinia/nuxt', '@nuxt/ui', '@nuxtjs/i18n', '@vueuse/nuxt'],

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
        locales: [
            { code: 'fr', name: 'Français', language: 'fr-FR' },
            { code: 'en', name: 'English', language: 'en-US' },
        ],
        defaultLocale: 'fr',
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
