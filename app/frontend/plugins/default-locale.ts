export default defineNuxtPlugin({
    enforce: 'pre',
    setup() {
        const {
            public: { defaultLocale },
        } = useRuntimeConfig();
        if (!defaultLocale) return;

        if (import.meta.server) {
            // Inject into request headers so i18n's server-side getCookie() reads it
            const event = useRequestEvent();
            if (!event) return;
            const hasCookie = event.node.req.headers.cookie?.includes('i18n_locale=');
            if (!hasCookie) {
                const existing = event.node.req.headers.cookie;
                event.node.req.headers.cookie = existing
                    ? `i18n_locale=${defaultLocale}; ${existing}`
                    : `i18n_locale=${defaultLocale}`;
            }
        } else {
            // Set cookie so i18n's client-side useCookie() reads it instead of browser language
            const localeCookie = useCookie('i18n_locale');
            if (!localeCookie.value) {
                localeCookie.value = defaultLocale as string;
            }
        }
    },
});
