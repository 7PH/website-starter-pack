// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Calls /admin/impersonations and swaps in the returned token. Toasts and
 * navigates to '/' on success; toasts on failure.
 */
export function useAdminImpersonation() {
    const api = useApi();
    const auth = useAuth();
    const { showSuccess, showError } = useToastHelpers();

    async function impersonate(userId: number, label: string): Promise<void> {
        try {
            const response = await api.post<ImpersonationResponse>('/admin/impersonations', {
                user_id: userId,
            });
            auth.saveUserToken({
                access_token: response.access_token,
                token_parsed: response.token_parsed,
                user: response.user,
                token_type: 'bearer',
            });
            showSuccess('Impersonation started', `Now viewing as ${label}`);
            await navigateTo('/');
        } catch (error) {
            showError(error, 'core.errors.generic');
        }
    }

    return { impersonate };
}
