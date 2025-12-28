// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
    compatibilityDate: '2024-11-01',

    runtimeConfig: {
        public: {
            apiBase: '/api', // NUXT_PUBLIC_API_BASE - relative path, same origin
            // Umami Analytics (optional)
            umamiEnabled: false, // NUXT_PUBLIC_UMAMI_ENABLED
            umamiUrl: '', // NUXT_PUBLIC_UMAMI_URL
            umamiWebsiteId: '', // NUXT_PUBLIC_UMAMI_WEBSITE_ID
        },
    },

    modules: [
        '@pinia/nuxt',
        '@nuxt/ui',
        '@nuxtjs/i18n',
    ],

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
