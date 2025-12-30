<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
definePageMeta({
    middleware: ['auth'],
    auth: true,
});

const { t } = useI18n();
const { isPremium, loading, refresh } = useSubscription();
const stripe = useStripe();

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
                                {{
                                    isPremium ? t('core.billing.personalSubscription') : t('core.billing.upgradePrompt')
                                }}
                            </p>
                        </div>
                    </div>

                    <!-- Benefits Grid -->
                    <div v-if="!isPremium" class="benefits-grid">
                        <div v-for="benefit in benefits" :key="benefit.label" class="benefit-item">
                            <UIcon :name="benefit.icon" class="benefit-icon text-lg" />
                            <span>{{ benefit.label }}</span>
                        </div>
                    </div>

                    <!-- CTA Section -->
                    <div class="cta-section">
                        <template v-if="isPremium">
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
</style>
