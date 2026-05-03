// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Composable for Stripe billing integration.
 * Combines billing portal access with subscription state management.
 *
 * @example
 * const { isPremium, loading, openBillingPortal, refresh } = useStripe();
 *
 * // Check premium status (from JWT, no API call)
 * if (isPremium.value) {
 *     console.log('User is premium!');
 * }
 *
 * // Refresh subscription from Stripe API
 * await refresh();
 *
 * // Open billing portal
 * await openBillingPortal();
 */

import * as stripeApi from '~/utils/api/stripe';

export function useStripe() {
    const auth = useAuth();

    // Subscription state
    const plan = ref<string | null>(null);
    const expiresAt = ref<Date | null>(null);
    const cancelAtPeriodEnd = ref(false);
    const loading = ref(false);
    const error = ref<string | null>(null);

    // Premium status comes directly from the JWT token (no API call needed)
    const isPremium = computed(() => auth.user?.is_premium ?? false);

    function resetSubscription() {
        plan.value = null;
        expiresAt.value = null;
        cancelAtPeriodEnd.value = false;
    }

    /**
     * Fetch subscription status from Stripe API.
     * Updates plan/expiresAt and refreshes token if premium status changed.
     */
    async function refresh(): Promise<void> {
        if (!auth.isLoggedIn) {
            resetSubscription();
            return;
        }

        loading.value = true;
        error.value = null;

        try {
            const data = await stripeApi.getSubscriptionStatus();
            plan.value = data.plan ?? null;
            expiresAt.value = data.expires_at ? new Date(data.expires_at) : null;
            cancelAtPeriodEnd.value = data.cancel_at_period_end ?? false;

            // If premium status changed, refresh token to get updated value
            if (data.is_premium !== undefined && data.is_premium !== auth.user?.is_premium) {
                await auth.refreshToken();
            }
        } catch {
            // Stripe not configured or user has no stripe_id
            resetSubscription();
        } finally {
            loading.value = false;
        }
    }

    /**
     * Open the Stripe billing portal in a new tab.
     * Allows users to manage their subscription, update payment methods, etc.
     */
    async function openBillingPortal(): Promise<void> {
        const returnUrl = window.location.href;
        const response = await stripeApi.getBillingPortalUrl(returnUrl);

        if (response.url) {
            window.open(response.url, '_blank');
        }
    }

    watch(
        () => auth.isLoggedIn,
        (loggedIn) => {
            if (!loggedIn) resetSubscription();
        },
    );

    return {
        // Reactive state (readonly refs prevent external mutation)
        isPremium,
        plan: readonly(plan),
        expiresAt: readonly(expiresAt),
        cancelAtPeriodEnd: readonly(cancelAtPeriodEnd),
        loading: readonly(loading),
        error: readonly(error),

        refresh,
        openBillingPortal,
    };
}
