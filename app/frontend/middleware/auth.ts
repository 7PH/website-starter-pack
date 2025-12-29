// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Authentication middleware for protected routes.
 * Redirects to login page when accessing protected route while logged out.
 *
 * Usage in page:
 * definePageMeta({
 *   middleware: ['auth'],
 *   auth: true,
 * });
 */

export default defineNuxtRouteMiddleware((to) => {
    // Skip auth check on server - token is in localStorage, not available during SSR
    if (import.meta.server) {
        return;
    }

    const auth = useAuth();

    // Check if route requires authentication
    const authMeta = to.meta.auth;
    if (!authMeta) {
        return;
    }

    // Parse auth options
    const authOptions = typeof authMeta === 'object' ? authMeta : { required: true };
    const { required = true } = authOptions as {
        required?: boolean;
    };

    if (!required) {
        return;
    }

    // Check if user is logged in
    if (auth.isLoggedIn) {
        return;
    }

    // Redirect to login with return URL
    // Use external: true to force full page reload, ensuring correct layout renders
    return navigateTo(
        {
            path: '/login',
            query: { redirect: to.fullPath },
        },
        { external: true },
    );
});
