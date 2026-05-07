<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import { PREMIUM_SOURCE, useOrganizationStatus } from '~/composables/organizations/useOrganizationStatus';

const { t } = useI18n();
const stripe = useStripe();
const config = useRuntimeConfig();
const { isPremium, loading, refresh, cancelAtPeriodEnd, expiresAt } = stripe;
const { organizations, firstOrg, firstAdminOrg, premiumOrg, isOrgAdmin, isAdminOfPremiumOrg, premiumSource } =
    useOrganizationStatus();

const stripeEnabled = computed(() => String(config.public.stripeEnabled) === 'true');

const formattedExpiresAt = computed(() => {
    if (!expiresAt.value) return '';
    const d = expiresAt.value;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}/${month}/${day}`;
});

onMounted(() => refresh());

const {
    showSubscribeModal,
    plans,
    isLoadingPlans,
    subscribingPriceId,
    openSubscribeModal,
    subscribeToPlan,
    openBillingPortal,
} = useUserSubscription();

const openingPortal = ref(false);
async function onOpenBillingPortal() {
    openingPortal.value = true;
    try {
        await openBillingPortal();
    } finally {
        openingPortal.value = false;
    }
}

const sourceLabel = computed(() => {
    if (premiumSource.value === PREMIUM_SOURCE.BOTH && premiumOrg.value) {
        return t('core.billing.sourceBoth', { orgName: premiumOrg.value.organization_name });
    }
    if (premiumSource.value === PREMIUM_SOURCE.PERSONAL) {
        return t('core.billing.sourcePersonal');
    }
    if (premiumSource.value === PREMIUM_SOURCE.ORGANIZATION && premiumOrg.value) {
        return t('core.billing.sourceViaOrg', { orgName: premiumOrg.value.organization_name });
    }
    return t('core.billing.sourceNone');
});
</script>

<template>
    <div class="space-y-4">
        <div v-if="loading" class="loading">
            <USkeleton class="h-6 w-48 mb-2" />
            <USkeleton class="h-4 w-32" />
        </div>

        <UCard v-else>
            <div class="flex items-center gap-4 mb-4">
                <div class="icon-box" :class="isPremium ? 'premium' : 'free'">
                    <UIcon name="i-lucide-star" class="text-xl" />
                </div>
                <div class="flex-1">
                    <h3 class="heading">{{ t('core.billing.yourPremiumAccess') }}</h3>
                    <p class="source-line">
                        <span class="source-label">{{ t('core.billing.source') }}:</span>
                        <span>{{ sourceLabel }}</span>
                    </p>
                </div>
                <UBadge
                    :label="isPremium ? t('core.billing.premium') : t('core.billing.free')"
                    :color="isPremium ? 'warning' : 'neutral'"
                />
            </div>

            <UAlert
                v-if="
                    cancelAtPeriodEnd &&
                    (premiumSource === PREMIUM_SOURCE.PERSONAL || premiumSource === PREMIUM_SOURCE.BOTH)
                "
                color="warning"
                variant="subtle"
                icon="i-lucide-alert-triangle"
                :title="t('core.billing.subscriptionCanceling')"
                :description="t('core.billing.subscriptionCancelingDescription', { date: formattedExpiresAt })"
                class="mb-4"
            />

            <p v-if="premiumSource === PREMIUM_SOURCE.BOTH" class="hint">
                {{ t('core.billing.bothSourcesHint') }}
            </p>

            <p v-else-if="!isPremium && isOrgAdmin && firstAdminOrg" class="hint">
                {{ t('core.billing.youAreOrgOwner', { orgName: firstAdminOrg.organization_name }) }} —
                {{ t('core.billing.manageOrgPrompt') }}
            </p>

            <p v-else-if="!isPremium && firstOrg" class="hint">
                {{ t('core.billing.contactOrgOwners') }}
            </p>

            <div class="actions">
                <UButton
                    v-if="
                        stripeEnabled &&
                        (premiumSource === PREMIUM_SOURCE.PERSONAL || premiumSource === PREMIUM_SOURCE.BOTH)
                    "
                    :label="t('core.billing.managePersonalBilling')"
                    :loading="openingPortal"
                    icon="i-lucide-credit-card"
                    color="neutral"
                    variant="outline"
                    @click="onOpenBillingPortal"
                />

                <NuxtLink
                    v-if="isAdminOfPremiumOrg && premiumOrg"
                    :to="`/organizations/${premiumOrg.organization_id}?tab=billing`"
                >
                    <UButton
                        :label="t('core.billing.manageOrganization')"
                        icon="i-lucide-building-2"
                        color="neutral"
                        variant="outline"
                    />
                </NuxtLink>

                <NuxtLink
                    v-else-if="!isPremium && isOrgAdmin && firstAdminOrg"
                    :to="`/organizations/${firstAdminOrg.organization_id}?tab=billing`"
                >
                    <UButton :label="t('core.billing.manageOrganization')" icon="i-lucide-building-2" color="primary" />
                </NuxtLink>

                <UButton
                    v-if="stripeEnabled && !isPremium"
                    :label="t('core.billing.subscribePersonally')"
                    icon="i-lucide-sparkles"
                    :color="organizations.length > 0 ? 'neutral' : 'primary'"
                    :variant="organizations.length > 0 ? 'outline' : 'solid'"
                    @click="openSubscribeModal"
                />
            </div>
        </UCard>

        <AccountSubscribeModal
            v-model:open="showSubscribeModal"
            :plans="plans"
            :is-loading="isLoadingPlans"
            :subscribing-price-id="subscribingPriceId"
            @subscribe="subscribeToPlan"
        />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.loading {
    @apply p-4;
}

.icon-box {
    @apply w-12 h-12 rounded-full flex items-center justify-center;
}

.icon-box.premium {
    @apply bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-300;
}

.icon-box.free {
    @apply bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400;
}

.heading {
    @apply font-semibold text-gray-900 dark:text-gray-100 m-0;
}

.source-line {
    @apply text-sm text-gray-600 dark:text-gray-400 mt-1 flex items-center gap-1;
}

.source-label {
    @apply font-medium text-gray-700 dark:text-gray-300;
}

.hint {
    @apply text-sm text-gray-600 dark:text-gray-400 mb-4;
}

.actions {
    @apply flex flex-wrap gap-3;
}
</style>
