// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Admin middleware - protects admin routes.
 * Redirects non-admin users to home page.
 * Allows access when impersonating (only admins can impersonate).
 * CMS editors (CMS_ENABLED) may also reach /admin/cms/**; other admin pages send them there.
 */
export default defineNuxtRouteMiddleware(async (to) => {
    // Skip on server - auth state is only available client-side
    if (import.meta.server) {
        return;
    }

    const auth = useAuth();

    // Allow if admin or impersonating (impersonation requires admin)
    if (auth.isLoggedIn && (auth.user?.is_admin || auth.isImpersonating)) {
        return;
    }

    if (auth.isLoggedIn && isCmsEnabled() && to.path.startsWith('/admin/')) {
        // Awaited so a page reload does not bounce the editor before their rights are loaded.
        const { canEdit, ensureLoaded } = useCmsAccess();
        await ensureLoaded();
        if (canEdit.value) {
            if (to.path.startsWith('/admin/cms/')) return;
            useToast().add({ title: useNuxtApp().$i18n.t('cms.nav.adminOnly'), color: 'warning' });
            return navigateTo('/admin/cms/pages');
        }
    }

    return navigateTo('/');
});
