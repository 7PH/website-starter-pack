<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import OrganizationsCreateModalDefault from '~/components/organizations/CreateModal.vue';
import OrganizationsPageActionsDefault from '~/components/organizations/PageActions.vue';

definePageMeta({
    middleware: ['auth'],
});

// Overridable components - sub-apps can replace these via config/component-overrides.ts
const OrganizationsCreateModal = useOverridable('OrganizationsCreateModal', OrganizationsCreateModalDefault);
const OrganizationsPageActions = useOverridable('OrganizationsPageActions', OrganizationsPageActionsDefault);

const auth = useAuth();
const api = useApi();
const modal = useModalStore();
const router = useRouter();
const { t } = useI18n();
const { showSuccess, showError } = useToastHelpers();
const config = useRuntimeConfig();

// Fetch user's organizations
const {
    data: organizations,
    pending,
    refresh,
} = await useAsyncData<UserOrganizationInfo[]>(
    'user-organizations-page',
    async () => {
        const userData = await api.get<UserRead>('/users/me');
        return userData.organizations || [];
    },
    { server: false },
);

const isLeaving = ref<number | null>(null);

// Create organization
const canCreateOrg = computed(() => config.public.orgSelfServiceCreation);
const showCreateModal = ref(false);
const isCreating = ref(false);

async function createOrganization(formData: {
    name: string;
    email: string;
    description: string;
    custom_data: OrganizationCustomData;
}) {
    isCreating.value = true;
    try {
        const newOrg = await api.post<OrganizationRead>('/organizations', formData);
        showSuccess(
            t('core.organizations.createSuccess'),
            t('core.organizations.createSuccessDescription', { name: formData.name }),
        );
        showCreateModal.value = false;
        await auth.refreshToken();
        router.push(`/organizations/${newOrg.id}`);
    } catch (error: unknown) {
        showError(error, 'core.organizations.createFailed');
    } finally {
        isCreating.value = false;
    }
}

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
    <div class="page-box">
        <UiPageTitleBanner compact>
            {{ t('core.organizations.title') }}
            <template #subtitle>
                {{ t('core.organizations.description') }}
            </template>
        </UiPageTitleBanner>

        <div class="organizations-content">
            <OrganizationsPageActions :can-create-org="canCreateOrg" @create="showCreateModal = true" />

            <!-- Loading state -->
            <div v-if="pending" class="loading-state">
                <UIcon name="i-lucide-loader-2" class="animate-spin text-4xl text-primary-500" />
            </div>

            <!-- No organizations -->
            <EmptyState
                v-else-if="!organizations || organizations.length === 0"
                icon="i-lucide-building-2"
                :title="t('core.organizations.noOrganizations')"
                :description="canCreateOrg ? t('core.organizations.noOrganizationsHint') : undefined"
            >
                <template v-if="canCreateOrg" #action>
                    <UButton
                        :label="t('core.organizations.createOrganization')"
                        icon="i-lucide-plus"
                        @click="showCreateModal = true"
                    />
                </template>
            </EmptyState>

            <!-- Organizations grid -->
            <div v-else class="org-grid">
                <OrganizationsCard
                    v-for="org in organizations"
                    :key="org.organization_id"
                    :organization="org"
                    :is-leaving="isLeaving === org.organization_id"
                    @leave="leaveOrganization(org)"
                />
            </div>
        </div>

        <!-- Create Organization Modal -->
        <OrganizationsCreateModal
            v-model:open="showCreateModal"
            :is-creating="isCreating"
            @create="createOrganization"
        />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.organizations-content {
    @apply max-w-5xl mx-auto;
}

.loading-state {
    @apply flex justify-center py-16;
}

.org-grid {
    @apply grid gap-4;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}
</style>
