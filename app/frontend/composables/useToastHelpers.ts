// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { getErrorMessage } from '~/utils/errors';

// Default durations
const SUCCESS_DURATION = 3000;
const ERROR_DURATION = 5000;

/**
 * Composable for consistent toast notifications.
 * Provides helpers for success and error toasts with standard formatting.
 */
export function useToastHelpers() {
    const toast = useToast();
    const { t } = useI18n();

    /**
     * Show a success toast notification.
     */
    function showSuccess(title: string, description?: string) {
        toast.add({
            title,
            description,
            color: 'success',
            duration: SUCCESS_DURATION,
        });
    }

    /**
     * Show an error toast notification.
     * Extracts message from Error instances or uses fallback.
     *
     * @param error - The caught error (unknown type)
     * @param fallbackKey - i18n key to use if error is not an Error instance
     */
    function showError(error: unknown, fallbackKey: string) {
        const message = getErrorMessage(error, t(fallbackKey));
        toast.add({
            title: t('core.errors.generic'),
            description: message,
            color: 'error',
            duration: ERROR_DURATION,
        });
    }

    /**
     * Show an error toast with a custom title.
     */
    function showErrorWithTitle(title: string, error: unknown, fallbackKey: string) {
        const message = getErrorMessage(error, t(fallbackKey));
        toast.add({
            title,
            description: message,
            color: 'error',
            duration: ERROR_DURATION,
        });
    }

    return {
        showSuccess,
        showError,
        showErrorWithTitle,
    };
}
