// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Admin middleware - protects admin routes.
 * Redirects non-admin users to home page.
 * Allows access when impersonating (only admins can impersonate).
 */
export default defineNuxtRouteMiddleware(() => {
    // Skip on server - auth state is only available client-side
    if (import.meta.server) {
        return;
    }

    const auth = useAuth();

    // Allow if admin or impersonating (impersonation requires admin)
    if (!auth.isLoggedIn || (!auth.user?.is_admin && !auth.isImpersonating)) {
        return navigateTo('/');
    }
});
