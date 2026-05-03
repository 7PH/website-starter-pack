// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Pinia store holding the backend's public /config snapshot.
 *
 * Populated once at app startup by plugins/backend-config.ts. On SSR the state
 * is auto-serialized into the Nuxt payload and rehydrated on the client,
 * so init() short-circuits client-side after a successful server fetch.
 *
 * Named `useBackendConfig` (not `useAppConfig`) to avoid colliding with
 * Nuxt's built-in `useAppConfig()` that reads `app.config.ts`.
 */
export const useBackendConfig = defineStore('backendConfig', () => {
    const config = ref<BackendConfig | null>(null);

    async function init() {
        if (config.value !== null) return; // Already hydrated from SSR payload
        const api = useApi();
        try {
            config.value = await api.fetch<BackendConfig>('/config', { retries: 3 });
        } catch {
            // Leave null; consumers fall back to defaults.
        }
    }

    return { config, init };
});
