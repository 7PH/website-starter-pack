import { defineStore } from 'pinia';

export const STORAGE_TOKEN_KEY = 'user-token';


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
         * Try and load the user token from local storage. If it's invalid, clear it.
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
                // Temporarily make the frontend think we're logged in
                this.token = token;
            } catch (error) {
                this.logout();
            }
        },

        /**
         * Logout the user
         */
        logout(): void {
            localStorage.removeItem(STORAGE_TOKEN_KEY);
            this.token = null;
        },

        /**
         * Save a token to local storage and update user information
         * @param token - The user token to save
         */
        saveUserToken(token: UserTokenUpdate): void {
            this.token = token;
            localStorage.setItem(STORAGE_TOKEN_KEY, JSON.stringify(token));
        },
    },
});