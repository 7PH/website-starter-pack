// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

export interface SubscriptionStatus {
    is_premium: boolean;
    plan: string | null;
    expires_at: string | null;
}

/**
 * Composable for Stripe billing integration.
 *
 * @example
 * const { openBillingPortal, getSubscriptionStatus } = useStripe();
 *
 * // Open billing portal
 * await openBillingPortal();
 *
 * // Check subscription status
 * const status = await getSubscriptionStatus();
 * if (status.is_premium) {
 *     console.log('User is premium!');
 * }
 */
export function useStripe() {
    const api = useApi();

    /**
     * Open the Stripe billing portal in a new tab.
     * Allows users to manage their subscription, update payment methods, etc.
     */
    async function openBillingPortal(): Promise<void> {
        const returnUrl = window.location.href;

        const response = await api.get<{ url: string }>(
            `/stripe/portal?return_url=${encodeURIComponent(returnUrl)}`,
        );

        if (response.url) {
            window.open(response.url, '_blank');
        }
    }

    /**
     * Get the current user's subscription status.
     */
    async function getSubscriptionStatus(): Promise<SubscriptionStatus> {
        return api.get<SubscriptionStatus>('/stripe/subscription');
    }

    return {
        openBillingPortal,
        getSubscriptionStatus,
    };
}
