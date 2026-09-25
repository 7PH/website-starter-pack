// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
// Default <title> from runtime config: nuxt.config's app.head.title is frozen at build time, and prod images are built without NUXT_PUBLIC_APP_NAME. Pages that set their own title still win.
export default defineNuxtPlugin(() => {
    useHead({ title: useRuntimeConfig().public.appName as string });
});
