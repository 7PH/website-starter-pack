// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * <html lang> follows the site's language, so screen readers and search engines read CMS pages in the right one.
 * No-op when CMS mode is off.
 */
export default defineNuxtPlugin((nuxtApp) => {
    if (!isCmsEnabled()) return;

    const i18n = nuxtApp.vueApp.config.globalProperties.$i18n;
    useHead({ htmlAttrs: { lang: () => i18n.locale } });
});
