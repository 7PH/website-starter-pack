// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { defineStore } from 'pinia';

export const STORAGE_TOKEN_KEY = 'user-token';
// Set when an owner uses "open as" on one of their managed accounts. Holds
// the owner's original token so we can restore it on "back to my account".
export const STORAGE_OPEN_AS_PREVIOUS_KEY = 'user-token-before-open-as';

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

        isImpersonating(): boolean {
            return this.token?.token_parsed?.real_admin_id != null;
        },

        /**
         * True when the current token came from owner-initiated "open as" on a
         * managed account. The original owner token is stashed in localStorage
         * under STORAGE_OPEN_AS_PREVIOUS_KEY for `stopOpenAs()` to restore.
         */
        isOpenAsManagedAccount(): boolean {
            if (import.meta.server) return false;
            return !!localStorage.getItem(STORAGE_OPEN_AS_PREVIOUS_KEY);
        },
    },
    actions: {
        /**
         * Initialize auth state from localStorage on app startup (client-side
         * only). The token is already loaded synchronously via getInitialToken;
         * this just refreshes it to extend the session.
         */
        init(): Promise<void> {
            return this.refreshToken();
        },

        /**
         * Clear the user session and remove token from storage.
         */
        logout(): void {
            if (import.meta.server) {
                return;
            }
            localStorage.removeItem(STORAGE_TOKEN_KEY);
            localStorage.removeItem(STORAGE_OPEN_AS_PREVIOUS_KEY);
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

        /**
         * Update the user data in the current token without refreshing.
         * Useful after profile updates where we already have the fresh data.
         */
        updateUser(user: UserRead): void {
            if (!this.token) {
                return;
            }
            this.token = {
                ...this.token,
                user,
            };
            if (import.meta.server) {
                return;
            }
            localStorage.setItem(STORAGE_TOKEN_KEY, JSON.stringify(this.token));
        },

        /**
         * Begin owner "open as managed account" by stashing the current owner
         * token, then swapping in the freshly-minted managed-account token.
         */
        startOpenAs(newToken: UserTokenUpdate): void {
            if (this.token && !import.meta.server) {
                localStorage.setItem(STORAGE_OPEN_AS_PREVIOUS_KEY, JSON.stringify(this.token));
            }
            this.saveUserToken(newToken);
        },

        /**
         * Restore the owner token stashed by `startOpenAs`. No-op if nothing
         * is stashed.
         */
        stopOpenAs(): void {
            if (import.meta.server) return;
            const stashed = localStorage.getItem(STORAGE_OPEN_AS_PREVIOUS_KEY);
            if (!stashed) return;
            try {
                const previous = JSON.parse(stashed) as UserTokenUpdate;
                localStorage.removeItem(STORAGE_OPEN_AS_PREVIOUS_KEY);
                this.saveUserToken(previous);
            } catch {
                localStorage.removeItem(STORAGE_OPEN_AS_PREVIOUS_KEY);
            }
        },

        /**
         * Refresh the current token to get updated user data.
         * Useful after actions that change user state (e.g., subscription changes).
         */
        async refreshToken(): Promise<void> {
            if (import.meta.server || !this.token) {
                return;
            }

            try {
                const apiBase = useRuntimeConfig().public.apiBase;
                const freshToken = await $fetch<UserTokenUpdate>(`${apiBase}/users/me/token`, {
                    method: 'PUT',
                    headers: {
                        Authorization: `Bearer ${this.token.access_token}`,
                    },
                });
                this.saveUserToken(freshToken);
            } catch {
                // Token invalid or expired - logout
                this.logout();
            }
        },
    },
});
