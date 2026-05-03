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

function getDefaultOptions(): UnsavedChangesOptions {
    const { t } = useI18n();
    return {
        title: t('core.unsavedChanges.title'),
        message: t('core.unsavedChanges.message'),
        confirmText: t('core.unsavedChanges.leave'),
        cancelText: t('core.unsavedChanges.stay'),
    };
}

/**
 * Composable that warns users when they try to leave a page with unsaved changes.
 * Handles both Vue Router navigation and browser tab close/refresh.
 *
 * Returns `checkBeforeLeave` for programmatic navigation: call it to await user
 * confirmation and only navigate if it resolves true.
 *
 * @param hasUnsavedChanges - Reactive ref or function that returns true if there are unsaved changes
 * @param options - Customization options for the warning modal
 *
 * @example
 * const isDirty = ref(false);
 * const { checkBeforeLeave } = useUnsavedChangesWarning(isDirty);
 *
 * async function handleCustomNavigation() {
 *     if (await checkBeforeLeave()) navigateTo('/somewhere');
 * }
 */
export function useUnsavedChangesWarning(
    hasUnsavedChanges: Ref<boolean> | (() => boolean),
    options: UnsavedChangesOptions = {},
) {
    const modal = useModalStore();
    const opts = { ...getDefaultOptions(), ...options };

    const isDirty = (): boolean =>
        typeof hasUnsavedChanges === 'function' ? hasUnsavedChanges() : hasUnsavedChanges.value;

    async function confirmLeave(): Promise<boolean> {
        return (
            (await modal.open<boolean>('confirm', {
                title: opts.title,
                message: opts.message,
                confirmText: opts.confirmText,
                cancelText: opts.cancelText,
                confirmColor: 'error',
            } as ConfirmModalOptions)) ?? false
        );
    }

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
        if (isDirty()) {
            event.preventDefault();
            // Modern browsers ignore custom messages, but we need to return something
            event.returnValue = opts.message!;
            return opts.message;
        }
    };

    onMounted(() => {
        if (import.meta.client) window.addEventListener('beforeunload', handleBeforeUnload);
    });
    onUnmounted(() => {
        if (import.meta.client) window.removeEventListener('beforeunload', handleBeforeUnload);
    });

    onBeforeRouteLeave(async (_to, _from, next) => {
        if (!isDirty()) return next();
        next((await confirmLeave()) ? undefined : false);
    });

    async function checkBeforeLeave(): Promise<boolean> {
        return isDirty() ? confirmLeave() : true;
    }

    return { checkBeforeLeave };
}
