<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatInterval, formatPrice } from '~/utils/formatters';

defineProps<{
    open: boolean;
    plans: StripePlan[];
    isLoading: boolean;
    subscribingPriceId: string | null;
}>();

const emit = defineEmits<{
    'update:open': [value: boolean];
    subscribe: [plan: StripePlan];
}>();

const { t } = useI18n();
</script>

<template>
    <UModal :open="open" @update:open="emit('update:open', $event)">
        <template #content>
            <UCard>
                <template #header>
                    <div class="modal-header">
                        <h3 class="modal-title">{{ t('core.billing.subscribeToPlan') }}</h3>
                        <UButton
                            icon="i-lucide-x"
                            color="neutral"
                            variant="ghost"
                            size="xs"
                            @click="emit('update:open', false)"
                        />
                    </div>
                </template>

                <div v-if="isLoading" class="flex justify-center py-8">
                    <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-primary-500" />
                </div>

                <div v-else-if="plans.length === 0" class="text-center py-8 text-gray-500">
                    {{ t('core.billing.noPlanAvailable') }}
                </div>

                <div v-else class="plans-grid">
                    <div v-for="plan in plans" :key="plan.price_id" class="plan-card">
                        <div class="plan-name">{{ plan.name }}</div>
                        <div class="plan-price">
                            <span class="plan-amount">{{ formatPrice(plan.amount, plan.currency) }}</span>
                            <span class="plan-period">{{ formatInterval(plan.interval) }}</span>
                        </div>
                        <UButton
                            :label="t('core.billing.selectPlan')"
                            class="mt-4 w-full"
                            :loading="subscribingPriceId === plan.price_id"
                            :disabled="subscribingPriceId !== null && subscribingPriceId !== plan.price_id"
                            @click="emit('subscribe', plan)"
                        />
                    </div>
                </div>
            </UCard>
        </template>
    </UModal>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.modal-header {
    @apply flex justify-between items-center;
}

.modal-title {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100;
}

.plans-grid {
    @apply grid gap-4;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.plan-card {
    @apply border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center min-w-0;
}

.plan-name {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100 truncate;
}

.plan-price {
    @apply mt-2 flex items-baseline justify-center gap-0.5 flex-wrap;
}

.plan-amount {
    @apply text-xl font-bold text-primary-500;
}

.plan-period {
    @apply text-sm text-gray-500 dark:text-gray-400;
}
</style>
