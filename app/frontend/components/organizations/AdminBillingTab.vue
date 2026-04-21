<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatDate, formatInterval, formatPrice } from '~/utils/formatters';

const props = defineProps<{
    orgId: number;
}>();

const { t } = useI18n();
const api = useApi();
const modal = useModalStore();
const { showSuccess, showError } = useToastHelpers();

const data = ref<OrganizationAdminBillingRead | null>(null);
const plans = ref<OrganizationPlan[]>([]);
const isLoading = ref(true);
const isLoadingPlans = ref(false);

const adjustAmount = ref<number | null>(null);
const adjustDescription = ref('');
const isAdjusting = ref(false);

const selectedPriceId = ref('');
const isAssigning = ref(false);
const isUnassigning = ref(false);

async function load() {
    isLoading.value = true;
    try {
        data.value = await api.get<OrganizationAdminBillingRead>(`/organizations/${props.orgId}/admin-billing`);
    } catch (error: unknown) {
        showError(error, 'core.organizations.adminBilling.loadFailed');
    } finally {
        isLoading.value = false;
    }
}

async function loadPlans() {
    if (plans.value.length) return;
    isLoadingPlans.value = true;
    try {
        plans.value = await api.get<OrganizationPlan[]>('/organizations/plans');
    } finally {
        isLoadingPlans.value = false;
    }
}

const balanceCents = computed(() => data.value?.balance_cents ?? 0);
const currency = computed(() => data.value?.currency ?? 'eur');
const balanceLabel = computed(() => formatPrice(balanceCents.value, currency.value));
const balanceState = computed<'credit' | 'zero' | 'debt'>(() => {
    if (balanceCents.value > 0) return 'credit';
    if (balanceCents.value < 0) return 'debt';
    return 'zero';
});
const balanceClass = computed(() => {
    switch (balanceState.value) {
        case 'credit':
            return 'text-green-600 dark:text-green-400';
        case 'debt':
            return 'text-red-600 dark:text-red-400';
        default:
            return 'text-gray-600 dark:text-gray-400';
    }
});
const balanceHint = computed(() => {
    switch (balanceState.value) {
        case 'credit':
            return t('core.organizations.adminBilling.creditHint');
        case 'debt':
            return t('core.organizations.adminBilling.debtHint');
        default:
            return t('core.organizations.adminBilling.zeroHint');
    }
});

const currentPlan = computed(() => data.value?.plan ?? null);

const planOptions = computed(() =>
    plans.value.map((p) => ({
        value: p.price_id,
        label: `${p.name} — ${formatPrice(p.amount, p.currency)}${formatInterval(p.interval)} (${p.seats} ${t(
            'core.organizations.adminBilling.seats',
        )})`,
    })),
);

async function submitAdjustment() {
    if (!adjustAmount.value || !adjustDescription.value.trim()) return;
    isAdjusting.value = true;
    try {
        data.value = await api.post<OrganizationAdminBillingRead>(
            `/organizations/${props.orgId}/admin-billing/adjust`,
            {
                amount_cents: Math.round(adjustAmount.value * 100),
                description: adjustDescription.value.trim(),
            },
        );
        showSuccess(t('core.organizations.adminBilling.adjustSuccess'));
        adjustAmount.value = null;
        adjustDescription.value = '';
    } catch (error: unknown) {
        showError(error, 'core.organizations.adminBilling.adjustFailed');
    } finally {
        isAdjusting.value = false;
    }
}

async function assignPlan() {
    if (!selectedPriceId.value) return;
    isAssigning.value = true;
    try {
        data.value = await api.post<OrganizationAdminBillingRead>(`/organizations/${props.orgId}/admin-billing/plan`, {
            price_id: selectedPriceId.value,
        });
        showSuccess(t('core.organizations.adminBilling.assignSuccess'));
        selectedPriceId.value = '';
    } catch (error: unknown) {
        showError(error, 'core.organizations.adminBilling.assignFailed');
    } finally {
        isAssigning.value = false;
    }
}

async function unassignPlan() {
    const confirmed = await modal.open('confirm', {
        title: t('core.organizations.adminBilling.unassignTitle'),
        message: t('core.organizations.adminBilling.unassignConfirm'),
        confirmText: t('core.organizations.adminBilling.unassign'),
        confirmColor: 'error',
    });
    if (!confirmed) return;
    isUnassigning.value = true;
    try {
        data.value = await api.delete<OrganizationAdminBillingRead>(`/organizations/${props.orgId}/admin-billing/plan`);
        showSuccess(t('core.organizations.adminBilling.unassignSuccess'));
    } catch (error: unknown) {
        showError(error, 'core.organizations.adminBilling.unassignFailed');
    } finally {
        isUnassigning.value = false;
    }
}

onMounted(() => {
    load();
    loadPlans();
});
</script>

<template>
    <div class="flex flex-col gap-6">
        <div v-if="isLoading" class="loading">
            <UIcon name="i-lucide-loader-2" class="animate-spin text-3xl text-primary-500" />
        </div>

        <template v-else-if="data">
            <!-- Balance -->
            <UCard>
                <template #header>
                    <UiCardHeader :title="t('core.organizations.adminBilling.balanceTitle')" />
                </template>
                <div class="balance" :class="balanceClass">
                    {{ balanceLabel }}
                </div>
                <p class="hint">{{ balanceHint }}</p>
            </UCard>

            <!-- Current plan -->
            <UCard>
                <template #header>
                    <UiCardHeader :title="t('core.organizations.adminBilling.planTitle')" />
                </template>
                <div v-if="currentPlan" class="flex flex-col gap-3">
                    <div class="plan-info">
                        <div class="plan-name">{{ currentPlan.name }}</div>
                        <div class="plan-price">
                            {{ formatPrice(currentPlan.amount, currentPlan.currency)
                            }}{{ formatInterval(currentPlan.interval) }}
                        </div>
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                        {{ t('core.organizations.adminBilling.seatsLabel', { seats: currentPlan.seats }) }}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                        {{
                            t('core.organizations.adminBilling.cycleLabel', {
                                start: formatDate(data.cycle_started_at),
                                end: formatDate(data.cycle_end),
                            })
                        }}
                    </div>
                    <div>
                        <UButton
                            :label="t('core.organizations.adminBilling.unassign')"
                            icon="i-lucide-x-circle"
                            color="error"
                            variant="outline"
                            :loading="isUnassigning"
                            @click="unassignPlan"
                        />
                    </div>
                </div>
                <div v-else class="flex flex-col gap-3">
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        {{ t('core.organizations.adminBilling.noPlan') }}
                    </p>
                    <UFormField :label="t('core.organizations.adminBilling.planLabel')">
                        <USelect
                            v-model="selectedPriceId"
                            :items="planOptions"
                            :loading="isLoadingPlans"
                            class="w-full"
                        />
                    </UFormField>
                    <div>
                        <UButton
                            :label="t('core.organizations.adminBilling.assign')"
                            icon="i-lucide-check-circle"
                            color="primary"
                            :loading="isAssigning"
                            :disabled="!selectedPriceId"
                            @click="assignPlan"
                        />
                    </div>
                </div>
            </UCard>

            <!-- Adjustment form -->
            <UCard>
                <template #header>
                    <UiCardHeader :title="t('core.organizations.adminBilling.adjustTitle')" />
                </template>
                <div class="flex flex-col gap-3">
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        {{ t('core.organizations.adminBilling.adjustHint', { currency: currency.toUpperCase() }) }}
                    </p>
                    <UFormField :label="t('core.organizations.adminBilling.amountLabel')">
                        <UInput v-model="adjustAmount" type="number" step="0.01" class="w-full" />
                    </UFormField>
                    <UFormField :label="t('core.organizations.adminBilling.descriptionLabel')">
                        <UInput v-model="adjustDescription" :maxlength="255" class="w-full" />
                    </UFormField>
                    <div>
                        <UButton
                            :label="t('core.organizations.adminBilling.recordAdjustment')"
                            icon="i-lucide-plus-circle"
                            color="primary"
                            :loading="isAdjusting"
                            :disabled="!adjustAmount || !adjustDescription.trim()"
                            @click="submitAdjustment"
                        />
                    </div>
                </div>
            </UCard>

            <!-- Transactions -->
            <UCard>
                <template #header>
                    <UiCardHeader :title="t('core.organizations.adminBilling.transactionsTitle')" />
                </template>
                <div v-if="!(data.transactions ?? []).length" class="text-sm text-gray-500 dark:text-gray-400">
                    {{ t('core.organizations.adminBilling.noTransactions') }}
                </div>
                <table v-else class="tx-table">
                    <thead>
                        <tr>
                            <th>{{ t('core.organizations.adminBilling.txDate') }}</th>
                            <th>{{ t('core.organizations.adminBilling.txAmount') }}</th>
                            <th>{{ t('core.organizations.adminBilling.txDescription') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tx in data.transactions ?? []" :key="tx.id">
                            <td>{{ formatDate(tx.created_at) }}</td>
                            <td
                                :class="
                                    tx.amount_cents >= 0
                                        ? 'text-green-600 dark:text-green-400'
                                        : 'text-red-600 dark:text-red-400'
                                "
                            >
                                {{ formatPrice(tx.amount_cents, tx.currency) }}
                            </td>
                            <td>{{ tx.description || '-' }}</td>
                        </tr>
                    </tbody>
                </table>
            </UCard>
        </template>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.loading {
    @apply flex justify-center py-12;
}

.balance {
    @apply text-4xl font-semibold;
}

.hint {
    @apply text-sm text-gray-500 dark:text-gray-400 mt-2;
}

.plan-info {
    @apply flex items-baseline justify-between gap-4;
}

.plan-name {
    @apply text-lg font-medium;
}

.plan-price {
    @apply text-xl font-semibold text-primary-600 dark:text-primary-400;
}

.tx-table {
    @apply w-full text-sm;
}

.tx-table th {
    @apply text-left text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 pb-2 border-b border-gray-200 dark:border-gray-700;
}

.tx-table td {
    @apply py-2 border-b border-gray-100 dark:border-gray-800;
}
</style>
