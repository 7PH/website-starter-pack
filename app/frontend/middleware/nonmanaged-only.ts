// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Route guard: redirects managed accounts (auth_method='access_code') to the
 * homepage. Apply to pages that have no useful surface for a managed account
 * — `/account`, `/messages`, etc. Backend endpoints already 403; this just
 * keeps the kid from staring at an empty page.
 */
export default defineNuxtRouteMiddleware(() => {
    const auth = useAuth();
    if (auth.user?.auth_method === 'access_code') {
        return navigateTo('/');
    }
});
