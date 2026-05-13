// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import * as stripeApi from '~/utils/api/stripe';

/**
 * Composable for individual-user Stripe subscription management.
 *
 * Mirrors `useOrganizationSubscription` but for the user-account flow.
 * Use it from the account billing tab to drive the Subscribe modal and
 * the Manage-Billing portal redirect.
 */
export function useUserSubscription() {
    const showSubscribeModal = ref(false);
    const plans = ref<StripePlan[]>([]);
    const isLoadingPlans = ref(false);
    const subscribingPriceId = ref<string | null>(null);

    async function loadPlans(): Promise<StripePlan[]> {
        if (plans.value.length > 0) return plans.value;
        isLoadingPlans.value = true;
        try {
            plans.value = await stripeApi.getUserPlans();
            return plans.value;
        } finally {
            isLoadingPlans.value = false;
        }
    }

    async function openSubscribeModal() {
        showSubscribeModal.value = true;
        await loadPlans();
    }

    async function subscribeToPlan(plan: StripePlan) {
        subscribingPriceId.value = plan.price_id;
        try {
            const response = await stripeApi.createUserCheckoutSession(plan.price_id);
            const bridge = useNativeBridge();
            if (bridge.isNative()) {
                await bridge.openExternal(response.url);
            } else {
                window.location.href = response.url;
            }
        } finally {
            subscribingPriceId.value = null;
        }
    }

    async function openBillingPortal() {
        const response = await stripeApi.getBillingPortalUrl(window.location.href);
        if (!response.url) return;

        const bridge = useNativeBridge();
        if (bridge.isNative()) {
            await bridge.openExternal(response.url);
        } else {
            window.open(response.url, '_blank');
        }
    }

    return {
        showSubscribeModal,
        plans,
        isLoadingPlans,
        subscribingPriceId,
        loadPlans,
        openSubscribeModal,
        subscribeToPlan,
        openBillingPortal,
    };
}
