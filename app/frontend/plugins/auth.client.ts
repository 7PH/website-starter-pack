// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { STORAGE_TOKEN_KEY } from '~/stores/useAuth';

/**
 * Client-only plugin to initialize auth state from localStorage.
 * Runs before Vue renders to prevent auth UI flash.
 */
export default defineNuxtPlugin(() => {
    const auth = useAuth();

    // Synchronously load token from localStorage before render
    try {
        const item = localStorage.getItem(STORAGE_TOKEN_KEY);
        if (item) {
            const token = JSON.parse(item) as UserTokenUpdate;
            auth.token = token;
        }
    } catch {
        // Invalid token in storage, ignore
    }

    // Trigger async token refresh (fire and forget)
    auth.init();
});
