// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Loads CMS edit rights whenever the logged-in user changes (login, logout, impersonation).
 * No-op when CMS mode is off.
 */
export default defineNuxtPlugin(() => {
    if (!isCmsEnabled()) return;

    const auth = useAuth();
    const { refresh } = useCmsAccess();
    watch(() => auth.user?.id, refresh, { immediate: true });
});
