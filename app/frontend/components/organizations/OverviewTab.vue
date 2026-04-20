<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
const props = defineProps<{
    org: OrganizationRead;
    isOwner: boolean;
    isAdminView: boolean;
    canManageSubscription: boolean;
}>();

const emit = defineEmits<{
    goToTab: [tab: string];
}>();

const { t } = useI18n();

const ownerCount = computed(() => (props.org.members ?? []).filter((m) => m.is_admin).length);
</script>

<template>
    <div class="overview">
        <UCard>
            <template #header>
                <UiCardHeader :title="t('core.organizations.tabs.overview')" />
            </template>

            <div class="grid">
                <div class="stat">
                    <span class="stat-label">{{ t('core.organizations.members') }}</span>
                    <span class="stat-value">{{ org.member_count }}</span>
                </div>
                <div class="stat">
                    <UTooltip :text="t('core.organizations.roleTooltip')">
                        <span class="stat-label">{{ t('core.organizations.admin') }}</span>
                    </UTooltip>
                    <span class="stat-value">{{ ownerCount }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">{{ t('core.billing.subscription') }}</span>
                    <span class="stat-value">
                        <UBadge
                            v-if="org.stripe_premium"
                            :label="t('core.organizations.premium')"
                            color="warning"
                            size="sm"
                        />
                        <UBadge v-else :label="t('core.organizations.free')" color="neutral" size="sm" />
                    </span>
                </div>
                <div v-if="org.stripe_premium" class="stat">
                    <span class="stat-label">{{ t('core.organizations.premiumQuota') }}</span>
                    <span class="stat-value">
                        {{
                            t('core.organizations.seatsUsed', {
                                used: org.premium_member_count,
                                total: org.stripe_quota,
                            })
                        }}
                    </span>
                </div>
            </div>

            <div v-if="isOwner" class="shortcuts">
                <UButton
                    icon="i-lucide-users"
                    :label="t('core.organizations.members')"
                    color="neutral"
                    variant="outline"
                    @click="emit('goToTab', 'members')"
                />
                <UButton
                    v-if="canManageSubscription"
                    icon="i-lucide-credit-card"
                    :label="t('core.organizations.tabs.billing')"
                    color="neutral"
                    variant="outline"
                    @click="emit('goToTab', 'billing')"
                />
            </div>
        </UCard>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.overview {
    @apply space-y-4;
}

.grid {
    @apply grid gap-6 sm:grid-cols-2 lg:grid-cols-4;
}

.stat {
    @apply flex flex-col gap-1;
}

.stat-label {
    @apply text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400;
}

.stat-value {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100;
}

.shortcuts {
    @apply mt-6 flex flex-wrap gap-2;
}
</style>
