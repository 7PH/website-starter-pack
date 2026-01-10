<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
import { PREMIUM_SOURCE, useOrganizationStatus } from '~/composables/organizations/useOrganizationStatus';

definePageMeta({
    middleware: ['auth'],
    auth: true,
});

const { t } = useI18n();
const stripe = useStripe();
const { isPremium, loading, refresh, cancelAtPeriodEnd, expiresAt } = stripe;
const config = useRuntimeConfig();

// Organization status from composable
const {
    organizations,
    orgsWithPremiumSeat,
    firstOrg,
    firstAdminOrg,
    premiumOrg,
    hasPersonalSubscription,
    isOrgAdmin,
    isAdminOfPremiumOrg,
    premiumSource,
} = useOrganizationStatus();

// Format the expiry date for display (YYYY/MM/DD)
const formattedExpiresAt = computed(() => {
    if (!expiresAt.value) return '';
    const d = expiresAt.value;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}/${month}/${day}`;
});

// Redirect to home if Stripe is disabled
const stripeEnabled = String(config.public.stripeEnabled) === 'true';
if (!stripeEnabled) {
    navigateTo('/');
}

// Sync premium status with Stripe on page load
onMounted(() => refresh());

const openingPortal = ref(false);
async function openBillingPortal() {
    openingPortal.value = true;
    try {
        await stripe.openBillingPortal();
    } finally {
        openingPortal.value = false;
    }
}

// Benefits list
const benefits: { icon: string; label: string }[] = [];
</script>

<template>
    <div class="premium-page">
        <ClientOnly>
            <!-- Loading State -->
            <div v-if="loading" class="space-y-6">
                <UCard>
                    <div class="flex items-center gap-4">
                        <USkeleton class="w-20 h-20 rounded-full" />
                        <div class="flex-1">
                            <USkeleton class="w-48 h-6 mb-2" />
                            <USkeleton class="w-32 h-4" />
                        </div>
                    </div>
                </UCard>
            </div>

            <!-- Content -->
            <div v-else>
                <!-- Premium Status Card -->
                <UCard class="status-card" :class="{ 'is-premium': isPremium }">
                    <div class="status-header" :class="isPremium ? 'premium' : 'free'">
                        <div class="status-icon">
                            <UIcon name="i-lucide-star" class="text-3xl" />
                        </div>
                        <div class="status-info">
                            <h2 class="status-title">
                                {{ isPremium ? t('core.billing.youArePremium') : t('core.billing.freeAccount') }}
                            </h2>
                            <p class="status-subtitle">
                                <!-- Both personal subscription AND org seat -->
                                <template v-if="isPremium && premiumSource === PREMIUM_SOURCE.BOTH && premiumOrg">
                                    {{
                                        t('core.billing.premiumBothSources', { orgName: premiumOrg.organization_name })
                                    }}
                                </template>
                                <!-- Personal subscription only -->
                                <template v-else-if="isPremium && premiumSource === PREMIUM_SOURCE.PERSONAL">
                                    {{ t('core.billing.personalSubscription') }}
                                </template>
                                <!-- Org seat only -->
                                <template
                                    v-else-if="isPremium && premiumSource === PREMIUM_SOURCE.ORGANIZATION && premiumOrg"
                                >
                                    {{ t('core.billing.premiumViaOrg', { orgName: premiumOrg.organization_name }) }}
                                </template>
                                <!-- Premium but unknown source (fallback) -->
                                <template v-else-if="isPremium">
                                    {{ t('core.billing.premiumActive') }}
                                </template>
                                <!-- Free user -->
                                <template v-else>
                                    {{ t('core.billing.upgradePrompt') }}
                                </template>
                            </p>
                        </div>
                    </div>

                    <!-- Subscription cancellation warning -->
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
                        class="my-4"
                    />

                    <!-- Premium with BOTH sources - info box -->
                    <div
                        v-if="isPremium && premiumSource === PREMIUM_SOURCE.BOTH && premiumOrg"
                        class="org-premium-info"
                    >
                        <p class="text-gray-600 dark:text-gray-400">
                            {{ t('core.billing.premiumBothDescription') }}
                        </p>
                    </div>

                    <!-- Premium via Organization only - extra info -->
                    <div
                        v-else-if="isPremium && premiumSource === PREMIUM_SOURCE.ORGANIZATION"
                        class="org-premium-info"
                    >
                        <p class="text-gray-600 dark:text-gray-400">
                            {{ t('core.billing.premiumViaOrgDescription') }}
                        </p>
                    </div>

                    <!-- Free User - Org Admin -->
                    <div v-if="!isPremium && isOrgAdmin && firstAdminOrg" class="org-admin-info">
                        <p class="info-title">
                            {{ t('core.billing.youAreOrgAdmin', { orgName: firstAdminOrg.organization_name }) }}
                        </p>
                        <p class="text-gray-600 dark:text-gray-400 text-sm">
                            {{ t('core.billing.manageOrgPrompt') }}
                        </p>
                    </div>

                    <!-- Free User - Org Member Only -->
                    <div
                        v-if="!isPremium && !isOrgAdmin && organizations.length > 0 && firstOrg"
                        class="org-member-info"
                    >
                        <p class="info-title">
                            {{ t('core.billing.youAreOrgMember', { orgName: firstOrg.organization_name }) }}
                        </p>
                        <p class="text-gray-600 dark:text-gray-400 text-sm">
                            {{ t('core.billing.contactOrgAdmin') }}
                        </p>
                    </div>

                    <!-- Benefits Grid (for free users without org) -->
                    <div v-if="!isPremium && organizations.length === 0" class="benefits-grid">
                        <div v-for="benefit in benefits" :key="benefit.label" class="benefit-item">
                            <UIcon :name="benefit.icon" class="benefit-icon text-lg" />
                            <span>{{ benefit.label }}</span>
                        </div>
                    </div>

                    <!-- CTA Section -->
                    <div class="cta-section">
                        <!-- Premium with BOTH sources -->
                        <template v-if="isPremium && premiumSource === PREMIUM_SOURCE.BOTH">
                            <div class="cta-group">
                                <UButton
                                    :label="t('core.billing.managePersonalBilling')"
                                    :loading="openingPortal"
                                    icon="i-lucide-credit-card"
                                    color="neutral"
                                    variant="outline"
                                    @click="openBillingPortal"
                                />
                                <NuxtLink
                                    v-if="isAdminOfPremiumOrg && premiumOrg"
                                    :to="`/organizations/${premiumOrg.organization_id}`"
                                >
                                    <UButton
                                        :label="t('core.billing.manageOrganization')"
                                        icon="i-lucide-building-2"
                                        color="neutral"
                                        variant="outline"
                                    />
                                </NuxtLink>
                            </div>
                        </template>

                        <!-- Premium with personal subscription only -->
                        <template v-else-if="isPremium && premiumSource === PREMIUM_SOURCE.PERSONAL">
                            <UButton
                                :label="t('core.billing.manage')"
                                :loading="openingPortal"
                                icon="i-lucide-external-link"
                                trailing
                                color="neutral"
                                variant="outline"
                                @click="openBillingPortal"
                            />
                        </template>

                        <!-- Premium via organization only -->
                        <template v-else-if="isPremium && premiumSource === PREMIUM_SOURCE.ORGANIZATION && premiumOrg">
                            <NuxtLink v-if="isAdminOfPremiumOrg" :to="`/organizations/${premiumOrg.organization_id}`">
                                <UButton
                                    :label="t('core.billing.manageOrganization')"
                                    icon="i-lucide-building-2"
                                    color="neutral"
                                    variant="outline"
                                />
                            </NuxtLink>
                        </template>

                        <!-- Premium but unknown source (fallback - just show manage billing) -->
                        <template v-else-if="isPremium">
                            <UButton
                                :label="t('core.billing.manage')"
                                :loading="openingPortal"
                                icon="i-lucide-external-link"
                                trailing
                                color="neutral"
                                variant="outline"
                                @click="openBillingPortal"
                            />
                        </template>

                        <!-- Free user - org admin -->
                        <template v-else-if="!isPremium && isOrgAdmin && firstAdminOrg">
                            <div class="cta-group">
                                <NuxtLink :to="`/organizations/${firstAdminOrg.organization_id}`">
                                    <UButton
                                        :label="t('core.billing.manageOrganization')"
                                        icon="i-lucide-building-2"
                                        color="primary"
                                    />
                                </NuxtLink>
                                <div class="cta-divider">
                                    <span class="text-gray-500 dark:text-gray-400 text-sm">
                                        {{ t('core.billing.orPersonalSubscription') }}
                                    </span>
                                </div>
                                <UButton
                                    :label="t('core.billing.subscribePersonally')"
                                    :loading="openingPortal"
                                    icon="i-lucide-sparkles"
                                    color="neutral"
                                    variant="outline"
                                    @click="openBillingPortal"
                                />
                            </div>
                        </template>

                        <!-- Free user - org member only -->
                        <template v-else-if="!isPremium && organizations.length > 0">
                            <UiGradientButton size="lg" :loading="openingPortal" @click="openBillingPortal">
                                <UIcon name="i-lucide-sparkles" class="mr-2" />
                                {{ t('core.billing.subscribePersonally') }}
                            </UiGradientButton>
                        </template>

                        <!-- Free user - no org -->
                        <template v-else>
                            <UiGradientButton size="lg" :loading="openingPortal" @click="openBillingPortal">
                                <UIcon name="i-lucide-sparkles" class="mr-2" />
                                {{ t('core.billing.subscribe') }}
                            </UiGradientButton>
                        </template>
                    </div>
                </UCard>
            </div>

            <!-- SSR Fallback -->
            <template #fallback>
                <UCard>
                    <div class="flex items-center gap-4">
                        <USkeleton class="w-20 h-20 rounded-full" />
                        <div class="flex-1">
                            <USkeleton class="w-48 h-6 mb-2" />
                            <USkeleton class="w-32 h-4" />
                        </div>
                    </div>
                </UCard>
            </template>
        </ClientOnly>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.premium-page {
    @apply max-w-2xl mx-auto py-8 px-4;
}

.status-card {
    @apply overflow-hidden;
}

/* Status Header */
.status-header {
    @apply flex items-center gap-4 p-6 -m-6 mb-6 rounded-t-xl;
}

.status-header.premium {
    background: linear-gradient(135deg, theme('colors.amber.400'), theme('colors.orange.500'));
}

.status-header.free {
    background: linear-gradient(
        135deg,
        theme('colors.accent.500'),
        theme('colors.primary.500'),
        theme('colors.pop.500')
    );
}

.status-icon {
    @apply w-16 h-16 rounded-full flex items-center justify-center;
    @apply bg-white/20 text-white;
}

.status-info {
    @apply flex-1;
}

.status-title {
    @apply text-xl font-bold text-white;
}

.status-subtitle {
    @apply text-sm text-white/80 mt-1;
}

/* Benefits Grid */
.benefits-grid {
    @apply grid grid-cols-2 gap-4 mb-6;
}

.benefit-item {
    @apply flex items-center gap-3 p-3 rounded-lg;
    @apply bg-gray-50 dark:bg-gray-800;
}

.benefit-icon {
    @apply text-primary-500;
}

/* CTA Section */
.cta-section {
    @apply flex justify-center pt-4;
}

.cta-group {
    @apply flex flex-col items-center gap-4;
}

.cta-divider {
    @apply text-center;
}

/* Org Info Sections */
.org-premium-info,
.org-admin-info,
.org-member-info {
    @apply mb-6 p-4 rounded-lg;
    @apply bg-gray-50 dark:bg-gray-800;
}

.info-title {
    @apply font-medium text-gray-900 dark:text-gray-100 mb-1;
}
</style>
