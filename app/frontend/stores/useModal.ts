// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { defineStore } from 'pinia';
import { nextTick } from 'vue';
import type { ModalOptions, ModalRecord } from '~/types/modal';

/**
 * Modal store for managing modal state across the application.
 * Provides a promise-based API for opening modals and awaiting their result.
 *
 * NOTE: Named useModalStore to avoid conflict with @nuxt/ui's useModal composable.
 *
 * @example
 * // In a modal component (e.g., ModalConfirm.vue)
 * const modal = useModalStore();
 * onMounted(() => modal.register('confirm'));
 *
 * // Opening from anywhere
 * const confirmed = await useModalStore().open<boolean>('confirm', {
 *     title: 'Are you sure?',
 *     message: 'This action cannot be undone.'
 * });
 * if (confirmed) {
 *     // User clicked confirm
 * }
 */
export const useModalStore = defineStore('modal', {
    state: () => ({
        modals: {} as Record<string, ModalRecord>,
    }),

    getters: {
        /**
         * Check if a modal is currently open.
         */
        isOpen:
            (state) =>
            (name: string): boolean => {
                return state.modals[name]?.open ?? false;
            },

        /**
         * Get the options for a modal.
         */
        getOptions:
            (state) =>
            (name: string): ModalOptions => {
                return state.modals[name]?.options ?? {};
            },
    },

    actions: {
        /**
         * Register a modal. Should be called in the modal component's onMounted.
         * @param name - Unique identifier for the modal
         * @param defaultOptions - Default options for this modal
         */
        register(name: string, defaultOptions: ModalOptions = {}): void {
            if (!this.modals[name]) {
                this.modals[name] = {
                    open: false,
                    options: defaultOptions,
                };
            } else if (this.modals[name].open) {
                // open() was called before register() - re-trigger open to ensure reactivity
                const pending = this.modals[name];
                this.modals[name] = {
                    open: false,
                    options: { ...defaultOptions, ...pending.options },
                    _resolve: pending._resolve,
                };
                // Re-open on next tick to trigger watchers
                nextTick(() => {
                    if (this.modals[name]) {
                        this.modals[name].open = true;
                    }
                });
            }
        },

        /**
         * Unregister a modal. Should be called in the modal component's onUnmounted.
         * @param name - Modal identifier
         */
        unregister(name: string): void {
            delete this.modals[name];
        },

        /**
         * Open a modal and wait for it to be closed.
         * @param name - Modal identifier
         * @param options - Options to pass to the modal
         * @returns Promise that resolves with the value passed to close()
         */
        open<T = unknown>(name: string, options: ModalOptions = {}): Promise<T> {
            return new Promise<T>((resolve) => {
                if (!this.modals[name]) {
                    // Modal not yet registered - create entry, it will be merged when register() is called
                    this.modals[name] = { open: false, options: {} };
                }

                this.modals[name] = {
                    open: true,
                    options: { ...this.modals[name].options, ...options },
                    _resolve: resolve as (value: unknown) => void,
                };
            });
        },

        /**
         * Close a modal and resolve its promise with a value.
         * @param name - Modal identifier
         * @param value - Value to resolve the promise with
         */
        close<T = unknown>(name: string, value?: T): void {
            const modal = this.modals[name];
            if (!modal) {
                return;
            }

            if (modal._resolve) {
                modal._resolve(value);
            }

            this.modals[name] = {
                open: false,
                options: {},
                _resolve: undefined,
            };
        },

        /**
         * Close all open modals.
         */
        closeAll(): void {
            for (const name of Object.keys(this.modals)) {
                if (this.modals[name]?.open) {
                    this.close(name, undefined);
                }
            }
        },
    },
});
