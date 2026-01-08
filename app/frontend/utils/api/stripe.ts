// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Stripe API service - mirrors backend/controllers/stripe.py
 * Raw API calls without UI concerns (no toasts, no store updates).
 */

/**
 * Get Stripe billing portal URL.
 */
export async function getBillingPortalUrl(returnUrl: string): Promise<BillingPortalResponse> {
    return useApi().get<BillingPortalResponse>(`/stripe/portal?return_url=${encodeURIComponent(returnUrl)}`);
}

/**
 * Get current user's subscription status.
 */
export async function getSubscriptionStatus(): Promise<SubscriptionStatus> {
    return useApi().get<SubscriptionStatus>('/stripe/subscription');
}
