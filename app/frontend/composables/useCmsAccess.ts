// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/** True when CMS mode is on (NUXT_PUBLIC_CMS_ENABLED). */
export function isCmsEnabled(): boolean {
    return String(useRuntimeConfig().public.cmsEnabled) === 'true';
}

// Module-level and written only in the browser (loads bail on the server), so it never leaks between SSR requests.
const isEditor = ref(false);
// Last load started, per user, so ensureLoaded() can reuse it instead of refetching.
let lastLoad: { userId: number | null; promise: Promise<void> } | null = null;

/**
 * CMS edit rights of the current user (CMS_ENABLED). Admins can always edit.
 * plugins/cms-access.client.ts calls refresh() when the user changes; ensureLoaded() waits for that load.
 *
 * @example
 * const { canEdit, isEditorOnly } = useCmsAccess();
 */
export function useCmsAccess() {
    const auth = useAuth();
    const cmsEnabled = isCmsEnabled();

    const canEdit = computed(() => cmsEnabled && auth.isLoggedIn && (!!auth.user?.is_admin || isEditor.value));
    // On admin pages: a CMS editor without admin rights, who only gets the CMS screens.
    const isEditorOnly = computed(() => cmsEnabled && !auth.user?.is_admin && !auth.isImpersonating);

    async function load(userId: number | null): Promise<void> {
        let value = false;
        if (userId !== null && !auth.user?.is_admin) {
            try {
                value = (await useApi().get<CmsMeRead>('/cms/me')).is_editor;
            } catch {
                // Treated as not an editor.
            }
        }
        // A newer load (another user) may have started meanwhile: it wins.
        if (lastLoad?.userId === userId) isEditor.value = value;
    }

    function refresh(): Promise<void> {
        if (import.meta.server || !cmsEnabled) return Promise.resolve();
        const userId = auth.user?.id ?? null;
        lastLoad = { userId, promise: load(userId) };
        return lastLoad.promise;
    }

    function ensureLoaded(): Promise<void> {
        return lastLoad?.userId === (auth.user?.id ?? null) ? lastLoad.promise : refresh();
    }

    return { canEdit, isEditorOnly, refresh, ensureLoaded };
}

/** Edit controls shown on the page itself (pencils, edit buttons). None in the admin: the preview there shows the editor's unsaved changes, a quick edit would save over them. */
export function useCmsEditInPlace() {
    const { canEdit } = useCmsAccess();
    const route = useRoute();
    return computed(() => canEdit.value && !route.path.startsWith('/admin'));
}
