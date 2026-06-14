<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
import { useOrganizationQuotaDisplay } from '~/composables/organizations/useOrganizationQuotaDisplay';

const props = defineProps<{
    org: OrganizationRead;
    canManageSubscription: boolean;
    isAdminView: boolean;
}>();

const emit = defineEmits<{
    openSubscribeModal: [];
    openBillingPortal: [];
}>();

const { t } = useI18n();
const orgRef = computed(() => props.org);
const { isOverQuota, progressColor, usedSeats, totalSeats, progressValue } = useOrganizationQuotaDisplay(orgRef);
</script>

<template>
    <UCard>
        <template #header>
            <UiCardHeader :title="t('core.organizations.tabs.billing')">
                <template #actions>
                    <template v-if="canManageSubscription && !org.deleted_at">
                        <UButton
                            v-if="org.stripe_premium"
                            :label="t('core.organizations.manageBilling')"
                            icon="i-lucide-credit-card"
                            size="sm"
                            color="neutral"
                            variant="outline"
                            @click="emit('openBillingPortal')"
                        />
                        <UButton
                            v-else
                            :label="t('core.organizations.subscribe')"
                            icon="i-lucide-sparkles"
                            size="sm"
                            color="primary"
                            @click="emit('openSubscribeModal')"
                        />
                    </template>
                </template>
            </UiCardHeader>
        </template>

        <div v-if="org.stripe_premium" class="space-y-4">
            <div>
                <div class="quota-header">
                    <span class="quota-label">{{
                        t('core.organizations.seatsUsedDetailed', { used: usedSeats, total: totalSeats })
                    }}</span>
                    <UBadge v-if="isOverQuota" :label="t('core.organizations.overQuota')" color="error" size="sm" />
                </div>
                <UProgress :model-value="progressValue" :color="progressColor" class="mt-2" />
            </div>

            <UAlert
                v-if="isOverQuota"
                color="warning"
                variant="subtle"
                icon="i-lucide-alert-triangle"
                :title="t('core.organizations.quotaExceeded')"
                :description="
                    t('core.organizations.quotaExceededDescription', {
                        used: usedSeats,
                        quota: totalSeats,
                    })
                "
            />
        </div>

        <div v-else class="empty">
            <p>{{ t('core.billing.upgradePrompt') }}</p>
        </div>
    </UCard>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.quota-header {
    @apply flex items-center justify-between;
}

.quota-label {
    @apply text-sm font-medium text-gray-700 dark:text-gray-300;
}

.empty {
    @apply text-sm text-gray-600 dark:text-gray-400;
}
</style>
