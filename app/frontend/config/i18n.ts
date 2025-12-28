// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import coreEn from '~/locales/core-en.json';
import coreFr from '~/locales/core-fr.json';
import appEn from '~/locales/en.json';
import appFr from '~/locales/fr.json';

// Deep merge helper
function deepMerge<T extends Record<string, unknown>>(target: T, source: T): T {
    const result = { ...target } as T;
    for (const key of Object.keys(source)) {
        const targetValue = result[key as keyof T];
        const sourceValue = source[key as keyof T];
        if (
            targetValue &&
            sourceValue &&
            typeof targetValue === 'object' &&
            typeof sourceValue === 'object' &&
            !Array.isArray(targetValue) &&
            !Array.isArray(sourceValue)
        ) {
            result[key as keyof T] = deepMerge(
                targetValue as Record<string, unknown>,
                sourceValue as Record<string, unknown>,
            ) as T[keyof T];
        } else {
            result[key as keyof T] = sourceValue;
        }
    }
    return result;
}

export default defineI18nConfig(() => ({
    legacy: false,
    locale: 'fr',
    fallbackLocale: 'fr',
    messages: {
        en: deepMerge(coreEn as Record<string, unknown>, appEn as Record<string, unknown>),
        fr: deepMerge(coreFr as Record<string, unknown>, appFr as Record<string, unknown>),
    },
}));
