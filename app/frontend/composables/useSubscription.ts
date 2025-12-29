// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Composable for user subscription status.
 * Uses is_premium from JWT token - no API call needed.
 * Call refresh() to sync with Stripe API if needed.
 */
export function useSubscription() {
    const api = useApi();
    const auth = useAuth();

    const plan = ref<string | null>(null);
    const expiresAt = ref<Date | null>(null);
    const loading = ref(false);
    const error = ref<string | null>(null);

    // Premium status comes directly from the JWT token
    const isPremium = computed(() => auth.user?.is_premium ?? false);

    async function fetchSubscription() {
        if (!auth.isLoggedIn) {
            plan.value = null;
            expiresAt.value = null;
            return;
        }

        loading.value = true;
        error.value = null;

        try {
            const data = (await api.get('/stripe/subscription')) as {
                is_premium?: boolean;
                plan?: string;
                expires_at?: string;
            };
            plan.value = data.plan ?? null;
            expiresAt.value = data.expires_at ? new Date(data.expires_at) : null;

            // If premium status changed, refresh token to get updated value
            if (data.is_premium !== undefined && data.is_premium !== auth.user?.is_premium) {
                await auth.refreshToken();
            }
        } catch (e) {
            // Stripe not configured or user has no stripe_id
            plan.value = null;
            expiresAt.value = null;
        } finally {
            loading.value = false;
        }
    }

    // Reset plan/expires when logged out
    watch(
        () => auth.isLoggedIn,
        (loggedIn) => {
            if (!loggedIn) {
                plan.value = null;
                expiresAt.value = null;
            }
        },
    );

    return {
        isPremium,
        plan: computed(() => plan.value),
        expiresAt: computed(() => expiresAt.value),
        loading: computed(() => loading.value),
        error: computed(() => error.value),
        refresh: fetchSubscription,
    };
}
