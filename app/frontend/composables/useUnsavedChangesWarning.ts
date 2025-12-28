// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { ConfirmModalOptions } from '~/types/modal';

export interface UnsavedChangesOptions {
    /** Modal title */
    title?: string;
    /** Modal message */
    message?: string;
    /** Confirm button text */
    confirmText?: string;
    /** Cancel button text */
    cancelText?: string;
}

const defaultOptions: UnsavedChangesOptions = {
    title: 'Unsaved changes',
    message: 'You have unsaved changes. Are you sure you want to leave this page?',
    confirmText: 'Leave',
    cancelText: 'Stay',
};

/**
 * Composable that warns users when they try to leave a page with unsaved changes.
 * Handles both Vue Router navigation and browser tab close/refresh.
 *
 * @param hasUnsavedChanges - Reactive ref or function that returns true if there are unsaved changes
 * @param options - Customization options for the warning modal
 *
 * @example
 * const isDirty = ref(false);
 *
 * // Simple usage with ref
 * useUnsavedChangesWarning(isDirty);
 *
 * // With custom messages
 * useUnsavedChangesWarning(isDirty, {
 *     title: 'Discard changes?',
 *     message: 'Your changes will be lost.',
 * });
 *
 * // With function
 * useUnsavedChangesWarning(() => form.isDirty);
 */
export function useUnsavedChangesWarning(
    hasUnsavedChanges: Ref<boolean> | (() => boolean),
    options: UnsavedChangesOptions = {},
): void {
    const modal = useModal();
    const router = useRouter();

    const mergedOptions = { ...defaultOptions, ...options };

    // Helper to check if there are unsaved changes
    const checkUnsaved = (): boolean => {
        return typeof hasUnsavedChanges === 'function'
            ? hasUnsavedChanges()
            : hasUnsavedChanges.value;
    };

    // Handle browser beforeunload (tab close, refresh, external navigation)
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
        if (checkUnsaved()) {
            event.preventDefault();
            // Modern browsers ignore custom messages, but we need to return something
            event.returnValue = mergedOptions.message!;
            return mergedOptions.message;
        }
    };

    // Register beforeunload handler
    onMounted(() => {
        if (import.meta.client) {
            window.addEventListener('beforeunload', handleBeforeUnload);
        }
    });

    onUnmounted(() => {
        if (import.meta.client) {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        }
    });

    // Handle Vue Router navigation
    onBeforeRouteLeave(async (_to, _from, next) => {
        if (!checkUnsaved()) {
            next();
            return;
        }

        // Show confirmation modal
        const confirmed = await modal.open<boolean>('confirm', {
            title: mergedOptions.title,
            message: mergedOptions.message,
            confirmText: mergedOptions.confirmText,
            cancelText: mergedOptions.cancelText,
            confirmColor: 'error',
        } as ConfirmModalOptions);

        if (confirmed) {
            next();
        } else {
            next(false);
        }
    });
}

/**
 * Same as useUnsavedChangesWarning but returns a function to manually trigger the check.
 * Useful when you need to check before programmatic navigation.
 *
 * @example
 * const { checkBeforeLeave } = useUnsavedChangesWarningManual(isDirty);
 *
 * async function handleCustomNavigation() {
 *     if (await checkBeforeLeave()) {
 *         // User confirmed or no changes
 *         navigateTo('/somewhere');
 *     }
 * }
 */
export function useUnsavedChangesWarningManual(
    hasUnsavedChanges: Ref<boolean> | (() => boolean),
    options: UnsavedChangesOptions = {},
) {
    // Set up the automatic guards
    useUnsavedChangesWarning(hasUnsavedChanges, options);

    const modal = useModal();
    const mergedOptions = { ...defaultOptions, ...options };

    const checkUnsaved = (): boolean => {
        return typeof hasUnsavedChanges === 'function'
            ? hasUnsavedChanges()
            : hasUnsavedChanges.value;
    };

    /**
     * Manually check if it's safe to leave.
     * Shows modal if there are unsaved changes.
     * @returns true if safe to leave (no changes or user confirmed)
     */
    async function checkBeforeLeave(): Promise<boolean> {
        if (!checkUnsaved()) {
            return true;
        }

        return await modal.open<boolean>('confirm', {
            title: mergedOptions.title,
            message: mergedOptions.message,
            confirmText: mergedOptions.confirmText,
            cancelText: mergedOptions.cancelText,
            confirmColor: 'error',
        } as ConfirmModalOptions) ?? false;
    }

    return {
        checkBeforeLeave,
    };
}
