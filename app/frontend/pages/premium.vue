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
</script>

<template>
    <div class="max-w-2xl mx-auto py-8 px-4">
        <!-- Page Title -->
        <h1 class="text-2xl font-bold mb-6 flex items-center gap-2">
            <i class="pi pi-star text-amber-400" />
            {{ t('core.billing.premium') }}
        </h1>

        <ClientOnly>
            <!-- Loading State -->
            <div v-if="loading" class="space-y-6">
                <Card>
                    <template #content>
                        <div class="flex items-center gap-4">
                            <Skeleton shape="circle" size="4rem" />
                            <div class="flex-1">
                                <Skeleton width="12rem" height="1.5rem" class="mb-2" />
                                <Skeleton width="8rem" height="1rem" />
                            </div>
                        </div>
                    </template>
                </Card>
                <Card>
                    <template #content>
                        <div class="flex items-center justify-between gap-4">
                            <div>
                                <Skeleton width="10rem" height="1.25rem" class="mb-2" />
                                <Skeleton width="14rem" height="1rem" />
                            </div>
                            <Skeleton width="6rem" height="2.5rem" />
                        </div>
                    </template>
                </Card>
            </div>

            <!-- Content -->
            <div v-else class="space-y-6">
                <!-- Status Card -->
                <Card>
                    <template #content>
                        <div class="flex items-center gap-4">
                            <!-- Premium Badge Icon -->
                            <div
                                class="w-16 h-16 rounded-full flex items-center justify-center shrink-0"
                                :class="isPremium ? 'bg-gradient-to-br from-amber-400 to-orange-500' : 'bg-gray-200'"
                            >
                                <i class="pi pi-star text-2xl" :class="isPremium ? 'text-white' : 'text-gray-400'" />
                            </div>

                            <div class="flex-1">
                                <h3 class="text-xl font-semibold">
                                    {{ isPremium ? t('core.billing.youArePremium') : t('core.billing.freeAccount') }}
                                </h3>
                                <p v-if="isPremium" class="text-sm text-gray-600 mt-1">
                                    <i class="pi pi-credit-card mr-1" />
                                    {{ t('core.billing.personalSubscription') }}
                                </p>
                                <p v-else class="text-sm text-gray-500 mt-1">
                                    {{ t('core.billing.upgradePrompt') }}
                                </p>
                            </div>
                        </div>
                    </template>
                </Card>

                <!-- CTA Card -->
                <Card>
                    <template #content>
                        <div class="flex items-center justify-between gap-4">
                            <div>
                                <h4 class="font-semibold">
                                    {{ isPremium ? t('core.billing.manageSubscription') : t('core.billing.upgrade') }}
                                </h4>
                                <p class="text-sm text-gray-500">
                                    {{
                                        isPremium ? t('core.billing.modifyOrCancel') : t('core.billing.unlockFeatures')
                                    }}
                                </p>
                            </div>
                            <Button
                                :label="isPremium ? t('core.billing.manage') : t('core.billing.subscribe')"
                                :loading="openingPortal"
                                icon="pi pi-external-link"
                                icon-pos="right"
                                @click="openBillingPortal"
                            />
                        </div>
                    </template>
                </Card>
            </div>

            <!-- SSR Fallback -->
            <template #fallback>
                <div class="space-y-6">
                    <Card>
                        <template #content>
                            <div class="flex items-center gap-4">
                                <Skeleton shape="circle" size="4rem" />
                                <div class="flex-1">
                                    <Skeleton width="12rem" height="1.5rem" class="mb-2" />
                                    <Skeleton width="8rem" height="1rem" />
                                </div>
                            </div>
                        </template>
                    </Card>
                    <Card>
                        <template #content>
                            <div class="flex items-center justify-between gap-4">
                                <div>
                                    <Skeleton width="10rem" height="1.25rem" class="mb-2" />
                                    <Skeleton width="14rem" height="1rem" />
                                </div>
                                <Skeleton width="6rem" height="2.5rem" />
                            </div>
                        </template>
                    </Card>
                </div>
            </template>
        </ClientOnly>
    </div>
</template>
