// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Stripe API service - mirrors backend/controllers/stripe.py
 * Raw API calls without UI concerns (no toasts, no store updates).
 */

/**
 * Get Stripe billing portal URL. Throws 400 if the user has no active sub.
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

/**
 * List user-tier plans from USER_STRIPE_PRICE_IDS.
 */
export async function getUserPlans(): Promise<StripePlan[]> {
    return useApi().get<StripePlan[]>('/stripe/plans');
}

/**
 * Create a Stripe checkout session for an individual subscription.
 * Returns the Stripe-hosted checkout URL.
 */
export async function createUserCheckoutSession(priceId: string): Promise<StripeCheckoutResponse> {
    return useApi().post<StripeCheckoutResponse>('/stripe/checkout', { price_id: priceId });
}
