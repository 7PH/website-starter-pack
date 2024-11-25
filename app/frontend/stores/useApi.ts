import { defineStore } from 'pinia';

export const useApi = defineStore('api', {
    actions: {
        /**
         * Fetch data from the API
         * @param path - The path to fetch data from
         * @param options - Fetch options
         * @returns Promise<T>
         */
        async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
            const authStore = useAuth();
            const basepath = import.meta.server ? 'http://backend:80' : useRuntimeConfig().public.apiBase;
            const response = await fetch(basepath + path, {
                ...options,
                headers: {
                    method: 'GET',
                    'Content-Type': 'application/json',
                    ...(authStore.isLoggedIn ? { Authorization: `Bearer ${authStore.token?.token_raw}` } : {}),
                    ...options.headers,
                },
            });
            if (!response.ok) {
                if (response.headers.get('WWW-Authenticate')?.includes('invalid_token')) {
                    authStore.logout();
                    throw new Error('Invalid or expired token');
                }
                try {
                    const error = await response.text();
                    throw new Error(error);
                } catch (error) {
                    if (error instanceof Error) {
                        throw error;
                    }
                }
                throw new Error(response.statusText || 'An error occurred');
            }
            return response.json();
        },

        /**
         * Fetch or fail (show error toast)
         * @param url - The URL to fetch data from
         * @param options - Fetch options
         * @returns Promise<T>
         */
        async fetchOrError<T>(url: string, options: RequestInit = {}): Promise<T> {
            try {
                return await this.fetch<T>(url, options);
            } catch (error) {
                const toast = useToast();
                if (error instanceof Error) {
                    toast.error(error.message);
                }
                throw error;
            }
        },
    },
});