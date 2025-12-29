// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

export type AvailableLocale = 'fr' | 'en';

/**
 * Composable for locale/language management.
 * Provides a simple API for building language switcher UIs.
 *
 * @example
 * const { locale, currentLocale, availableLocales, setLocale } = useLocale();
 *
 * // Switch to English
 * setLocale('en');
 *
 * // Get current locale name
 * console.log(currentLocale.value?.name); // "English"
 */
export function useLocale() {
    const { locale, locales, setLocale } = useI18n();

    const availableLocales = computed(() =>
        (locales.value as Array<AvailableLocale | { code: AvailableLocale; name: string }>).map((l) =>
            typeof l === 'string' ? { code: l, name: l } : l,
        ),
    );

    const currentLocale = computed(() => availableLocales.value.find((l) => l.code === locale.value));

    return {
        locale, // Current locale code (ref)
        currentLocale, // Current locale object { code, name }
        availableLocales, // All locales [{ code, name }, ...]
        setLocale, // Function to switch locale
    };
}
