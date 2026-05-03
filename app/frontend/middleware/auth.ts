// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Auth middleware. Pages opt in with `definePageMeta({ middleware: ['auth'], auth: true })`;
 * unauthenticated visitors are bounced to /login with ?redirect=<original path>.
 *
 * external: true forces a full reload so the auth layout renders cleanly.
 */
export default defineNuxtRouteMiddleware((to) => {
    // Token lives in localStorage — auth state isn't available during SSR.
    if (import.meta.server) return;
    if (!to.meta.auth) return;

    if (useAuth().isLoggedIn) return;

    return navigateTo({ path: '/login', query: { redirect: to.fullPath } }, { external: true });
});
