// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Client-side username validation using the pattern served on /config, so there
 * is one definition rather than a copy here that drifts. Instant feedback only;
 * the backend still enforces on every write.
 */
export function useUsernameRules() {
    const backendConfig = useBackendConfig();
    const { t } = useI18n();

    /** Returns a localized error message, or undefined when the handle is fine. */
    function validateUsername(raw: string): string | undefined {
        const username = raw.trim();
        if (!username) return t('core.validation.required');

        const pattern = backendConfig.config?.username_pattern;
        if (pattern && !new RegExp(pattern).test(username)) {
            return t('core.auth.usernameInvalid');
        }

        return undefined;
    }

    return { validateUsername };
}
