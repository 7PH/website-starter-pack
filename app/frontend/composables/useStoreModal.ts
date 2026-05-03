// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { ModalOptions } from '~/types/modal';

/**
 * Wires a modal component into `useModalStore` with SSR-safe accessors.
 *
 * Use inside a modal's `<script setup>`:
 *   const { isOpen, options, close } = useStoreModal<MyOptions>('my-modal');
 *
 * Closing via `isOpen = false` (e.g. backdrop click) resolves the modal's
 * promise with `false`. Pass an explicit value to `close()` to resolve with
 * something else (e.g. `close(true)` on confirm).
 */
export function useStoreModal<TOptions extends ModalOptions = ModalOptions>(name: string) {
    const modal = useModalStore();

    onMounted(() => modal.register(name));
    onUnmounted(() => modal.unregister(name));

    const isOpen = computed({
        get: () => {
            if (import.meta.server) return false;
            return modal.isOpen?.(name) ?? false;
        },
        set: (value: boolean) => {
            if (!value) close(false);
        },
    });

    const options = computed((): TOptions => {
        if (import.meta.server) return {} as TOptions;
        return (modal.getOptions?.(name) ?? {}) as TOptions;
    });

    function close<T = unknown>(value?: T): void {
        modal.close(name, value);
    }

    return { isOpen, options, close };
}
