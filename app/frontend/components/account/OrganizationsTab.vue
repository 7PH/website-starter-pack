<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
// Types from models.ts are declared globally

const auth = useAuth();
const api = useApi();
const modal = useModalStore();
const { t } = useI18n();
const { showSuccess, showError } = useToastHelpers();

// Fetch user's organizations
const {
    data: organizations,
    pending,
    refresh,
} = await useAsyncData<UserOrganizationInfo[]>(
    'user-organizations',
    async () => {
        // Get user data which includes organizations
        const userData = await api.get<UserRead>('/users/me');
        return userData.organizations || [];
    },
    { server: false },
);

const isLeaving = ref<number | null>(null);

async function leaveOrganization(org: UserOrganizationInfo) {
    const confirmed = await modal.open('confirm', {
        title: t('core.organizations.leaveTitle'),
        message: t('core.organizations.leaveConfirm', { name: org.organization_name }),
        confirmText: t('core.organizations.leave'),
        confirmColor: 'error',
    });

    if (!confirmed) return;

    isLeaving.value = org.organization_id;
    try {
        await api.delete(`/organizations/${org.organization_id}/members/me`);
        showSuccess(
            t('core.organizations.leftSuccess'),
            t('core.organizations.leftDescription', { name: org.organization_name }),
        );
        // Refresh user data to update the auth store
        await auth.refreshToken();
        refresh();
    } catch (error: unknown) {
        showError(error, 'core.organizations.leaveFailed');
    } finally {
        isLeaving.value = null;
    }
}
</script>

<template>
    <div class="space-y-6">
        <UCard>
            <template #header>
                <div>
                    <h2 class="text-lg font-semibold">{{ t('core.organizations.title') }}</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        {{ t('core.organizations.description') }}
                    </p>
                </div>
            </template>

            <!-- Loading state -->
            <div v-if="pending" class="flex justify-center py-8">
                <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-primary-500" />
            </div>

            <!-- No organizations -->
            <div v-else-if="!organizations || organizations.length === 0" class="text-center py-8">
                <UIcon name="i-lucide-building-2" class="text-4xl text-gray-400 dark:text-gray-500 mb-3" />
                <p class="text-gray-500 dark:text-gray-400">
                    {{ t('core.organizations.noOrganizations') }}
                </p>
            </div>

            <!-- Organizations list -->
            <div v-else class="space-y-4">
                <div v-for="org in organizations" :key="org.organization_id" class="org-item">
                    <div class="org-info">
                        <div class="org-name">{{ org.organization_name }}</div>
                        <UBadge
                            :label="org.is_admin ? t('core.organizations.admin') : t('core.organizations.member')"
                            :color="org.is_admin ? 'info' : 'neutral'"
                            size="xs"
                        />
                    </div>
                    <div class="org-actions">
                        <NuxtLink v-if="org.is_admin" :to="`/organizations/${org.organization_id}`">
                            <UButton
                                :label="t('core.organizations.manage')"
                                color="primary"
                                variant="ghost"
                                size="xs"
                            />
                        </NuxtLink>
                        <UButton
                            :label="t('core.organizations.leave')"
                            color="error"
                            variant="ghost"
                            size="xs"
                            :loading="isLeaving === org.organization_id"
                            @click="leaveOrganization(org)"
                        />
                    </div>
                </div>
            </div>
        </UCard>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.org-item {
    @apply flex items-center justify-between py-3 px-4;
    @apply border border-gray-200 dark:border-gray-700 rounded-lg;
}

.org-info {
    @apply flex items-center gap-3;
}

.org-name {
    @apply font-medium text-gray-900 dark:text-gray-100;
}

.org-actions {
    @apply flex items-center gap-2;
}
</style>
