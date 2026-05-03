// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Universal plugin (server + client): fetches /config once at app startup.
 *
 * On SSR, the fetched state is serialized into the Nuxt payload by
 * @pinia/nuxt and rehydrated on the client, so the client-side run of
 * init() short-circuits without a second HTTP call.
 */
export default defineNuxtPlugin(async () => {
    await useBackendConfig().init();
});
