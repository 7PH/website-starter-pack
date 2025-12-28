// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { defineStore } from 'pinia';

export const STORAGE_TOKEN_KEY = 'user-token';

/**
 * Authentication store for managing user sessions.
 * Handles token persistence in localStorage and provides auth state.
 */
export const useAuth = defineStore('auth', {
    state: () => ({
        token: null as UserTokenUpdate | null,
    }),
    getters: {
        isLoggedIn(): boolean {
            return !!this.token;
        },

        user(): UserRead | null {
            return this.token ? this.token.user : null;
        },
    },
    actions: {
        /**
         * Initialize auth state from localStorage.
         * Should be called on app startup (client-side only).
         */
        async init(): Promise<void> {
            if (import.meta.server) {
                return;
            }
            try {
                const item = localStorage.getItem(STORAGE_TOKEN_KEY);
                const token = item ? (JSON.parse(item) as UserTokenUpdate) : null;
                if (!token) {
                    return;
                }
                this.token = token;
            } catch (error) {
                this.logout();
            }
        },

        /**
         * Clear the user session and remove token from storage.
         */
        logout(): void {
            if (import.meta.server) {
                return;
            }
            localStorage.removeItem(STORAGE_TOKEN_KEY);
            this.token = null;
        },

        /**
         * Save a new token and update user state.
         * @param token - The authentication token response
         */
        saveUserToken(token: UserTokenUpdate): void {
            this.token = token;
            if (import.meta.server) {
                return;
            }
            localStorage.setItem(STORAGE_TOKEN_KEY, JSON.stringify(token));
        },
    },
});
