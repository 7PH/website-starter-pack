import { defineStore } from 'pinia';

/**
 * Toast store. Rendering is up to /components/layout/PageToastOverlay.vue
 */
export const useToast = defineStore('toast', {
    state: () => ({
        messages: [] as { type: 'error' | 'success'; message: string }[],
    }),
    actions: {
        error(message: string): void {
            this.messages.push({ type: 'error', message });
        },

        success(message: string): void {
            this.messages.push({ type: 'success', message });
        },
    },
});
