// https://nuxt.com/docs/api/configuration/nuxt-config
import Aura from '@primevue/themes/aura';

export default defineNuxtConfig({
    compatibilityDate: '2025-01-01',

    app: {
        head: {
            title: process.env.NUXT_PUBLIC_APP_NAME || 'My App',
        },
    },

    // Vite config for Docker/WSL2 file watching
    vite: {
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

    modules: ['@pinia/nuxt', '@nuxtjs/tailwindcss', '@primevue/nuxt-module', '@nuxtjs/i18n', '@nuxtjs/color-mode'],

    colorMode: {
        preference: 'system',
        fallback: 'light',
        classSuffix: '',
        storageKey: 'color-mode',
    },

    primevue: {
        options: {
            theme: {
                preset: Aura,
                options: {
                    darkModeSelector: '.dark',
                },
            },
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
