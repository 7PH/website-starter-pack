// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { Ref } from 'vue';

/**
 * Composable for managing organization subscriptions with Stripe.
 * Handles plan loading, checkout, billing portal, and subscription sync.
 */
export function useOrganizationSubscription(
    orgId: Ref<number>,
    org: Ref<OrganizationRead | null | undefined>,
    refreshOrg: () => void,
) {
    const api = useApi();

    const showSubscribeModal = ref(false);
    const plans = ref<OrganizationPlan[]>([]);
    const isLoadingPlans = ref(false);
    const subscribingPriceId = ref<string | null>(null);
    const hasSyncedSubscription = ref(false);

    /**
     * Load available organization plans from API.
     */
    async function loadPlans(): Promise<OrganizationPlan[]> {
        if (plans.value.length > 0) return plans.value;

        isLoadingPlans.value = true;
        try {
            plans.value = await api.get<OrganizationPlan[]>('/organizations/plans');
            return plans.value;
        } finally {
            isLoadingPlans.value = false;
        }
    }

    /**
     * Open the subscribe modal and load plans.
     */
    async function openSubscribeModal() {
        showSubscribeModal.value = true;
        await loadPlans();
    }

    /**
     * Create a checkout session for a plan and redirect to Stripe.
     */
    async function subscribeToPlan(plan: OrganizationPlan) {
        subscribingPriceId.value = plan.price_id;
        try {
            const response = await api.post<{ url: string }>(`/organizations/${orgId.value}/checkout`, {
                price_id: plan.price_id,
            });
            window.location.href = response.url;
        } finally {
            subscribingPriceId.value = null;
        }
    }

    /**
     * Open the Stripe billing portal in a new tab.
     */
    async function openBillingPortal() {
        const response = await api.get<{ url: string }>(`/organizations/${orgId.value}/portal`, {
            return_url: window.location.href,
        });
        window.open(response.url, '_blank');
    }

    /**
     * Sync subscription status with Stripe (handles webhook failures).
     */
    async function syncSubscription() {
        if (!org.value?.stripe_id) return;
        try {
            const status = await api.get<OrganizationSubscriptionStatus>(`/organizations/${orgId.value}/subscription`);
            if (
                org.value &&
                (org.value.stripe_premium !== status.stripe_premium || org.value.stripe_quota !== status.stripe_quota)
            ) {
                org.value.stripe_premium = status.stripe_premium;
                org.value.stripe_quota = status.stripe_quota;
            }
        } catch {
            // Silently fail - subscription sync is best-effort
        }
    }

    // Auto-sync subscription when org data loads (once)
    watch(
        org,
        (newOrg) => {
            if (newOrg?.stripe_id && !hasSyncedSubscription.value) {
                hasSyncedSubscription.value = true;
                syncSubscription();
            }
        },
        { immediate: true },
    );

    return {
        showSubscribeModal,
        plans,
        isLoadingPlans,
        subscribingPriceId,
        loadPlans,
        openSubscribeModal,
        subscribeToPlan,
        openBillingPortal,
        syncSubscription,
    };
}
