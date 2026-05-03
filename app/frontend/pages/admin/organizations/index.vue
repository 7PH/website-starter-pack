<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin'],
});

import { formatDate } from '~/utils/formatters';
import { DELETED_FILTER_OPTIONS, YES_NO_FILTER_OPTIONS, yesNoToBool } from '~/utils/admin-filters';

// Types from models.ts are declared globally

const api = useApi();
const { showSuccess, showError } = useToastHelpers();
const modal = useModalStore();

const { search, debouncedSearch: searchDebounced, page, limit, offset } = useTableState({ defaultLimit: 100 });

// Filters
const premiumFilter = ref('all');
const deletedFilter = ref('hide');

// useTableState resets page on debouncedSearch; reset on other filters too.
watch([premiumFilter, deletedFilter], () => {
    page.value = 1;
});

const {
    data: orgsData,
    pending,
    refresh,
} = await useAsyncData<OrganizationListResponse>(
    'admin-organizations',
    () =>
        api.get('/organizations', {
            search: searchDebounced.value || undefined,
            stripe_premium: yesNoToBool(premiumFilter.value),
            include_deleted: deletedFilter.value !== 'hide' ? true : undefined,
            only_deleted: deletedFilter.value === 'only' ? true : undefined,
            limit: limit.value,
            offset: offset.value,
        }),
    { watch: [searchDebounced, premiumFilter, deletedFilter, page], server: false },
);

const totalPages = computed(() => Math.ceil((orgsData.value?.total ?? 0) / limit.value));

// Table columns configuration
const columns = [
    { accessorKey: 'id', header: 'ID' },
    { accessorKey: 'name', header: 'Name' },
    { accessorKey: 'email', header: 'Email' },
    { accessorKey: 'members', header: 'Members' },
    { accessorKey: 'status', header: 'Status' },
    { accessorKey: 'created_at', header: 'Created' },
    { accessorKey: 'actions', header: 'Actions' },
];

// Type helper for table row access (UTable doesn't preserve generic types in slots)
function getOrg(row: { original: unknown }): OrganizationRead {
    return row.original as OrganizationRead;
}

// Create organization modal
const showCreateModal = ref(false);
const isCreating = ref(false);

async function createOrganization(formData: { name: string; email: string; description: string }) {
    isCreating.value = true;
    try {
        await api.post('/organizations', formData);
        showSuccess('Organization created', `${formData.name} has been created`);
        showCreateModal.value = false;
        refresh();
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        isCreating.value = false;
    }
}

async function deleteOrganization(org: OrganizationRead) {
    const confirmed = await modal.open('confirm', {
        title: 'Delete Organization',
        message: `Are you sure you want to delete ${org.name}? This action cannot be undone.`,
        confirmText: 'Delete',
        confirmColor: 'error',
    });

    if (!confirmed) return;

    try {
        await api.delete(`/organizations/${org.id}`);
        showSuccess('Organization deleted', `${org.name} has been deleted`);
        refresh();
    } catch (error) {
        showError(error, 'core.errors.generic');
    }
}
</script>

<template>
    <div class="page-box">
        <AdminPageBanner />

        <div class="admin-orgs">
            <div class="page-header">
                <div class="header-left">
                    <h1 class="page-title">Organizations</h1>
                    <span class="org-count">{{ orgsData?.total ?? 0 }} total</span>
                </div>
                <UButton label="Create Organization" icon="i-lucide-plus" @click="showCreateModal = true" />
            </div>

            <!-- Filters -->
            <div class="filters">
                <UInput
                    v-model="search"
                    placeholder="Search by name or email..."
                    icon="i-lucide-search"
                    class="search-input"
                />
                <div class="filter-item">
                    <label class="filter-label">Premium</label>
                    <USelect v-model="premiumFilter" :items="YES_NO_FILTER_OPTIONS" class="w-24" />
                </div>
                <div class="filter-item">
                    <label class="filter-label">Deleted</label>
                    <USelect v-model="deletedFilter" :items="DELETED_FILTER_OPTIONS" class="w-32" />
                </div>
            </div>

            <!-- Organizations Table -->
            <UCard :ui="{ body: 'p-0 sm:p-0' }">
                <UTable :columns="columns" :data="orgsData?.items ?? []" :loading="pending">
                    <template #name-cell="{ row }">
                        <NuxtLink :to="`/admin/organizations/${row.original.id}`" class="org-link">
                            {{ row.original.name }}
                        </NuxtLink>
                    </template>

                    <template #members-cell="{ row }">
                        <div class="member-info">
                            <span>{{ row.original.member_count }} members</span>
                            <span
                                v-if="
                                    row.original.stripe_premium &&
                                    (row.original.premium_member_count ?? 0) > row.original.stripe_quota
                                "
                                class="over-quota"
                            >
                                ({{ row.original.premium_member_count ?? 0 }}/{{ row.original.stripe_quota }}
                                premium - over quota!)
                            </span>
                            <span v-else-if="row.original.stripe_premium" class="quota-info">
                                ({{ row.original.premium_member_count ?? 0 }}/{{ row.original.stripe_quota }} premium)
                            </span>
                        </div>
                    </template>

                    <template #status-cell="{ row }">
                        <div class="status-badges">
                            <UBadge v-if="row.original.deleted_at" label="Deleted" color="error" />
                            <UBadge v-if="row.original.stripe_premium" label="Premium" color="warning" />
                            <UBadge
                                v-if="
                                    row.original.stripe_premium &&
                                    (row.original.premium_member_count ?? 0) > row.original.stripe_quota
                                "
                                label="Over Quota"
                                color="error"
                            />
                        </div>
                    </template>

                    <template #created_at-cell="{ row }">
                        {{ formatDate(row.original.created_at) }}
                    </template>

                    <template #actions-cell="{ row }">
                        <div v-if="!row.original.deleted_at" class="actions">
                            <UTooltip text="Edit">
                                <NuxtLink :to="`/admin/organizations/${row.original.id}`">
                                    <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" size="xs" />
                                </NuxtLink>
                            </UTooltip>
                            <UTooltip text="Delete">
                                <UButton
                                    icon="i-lucide-trash-2"
                                    color="error"
                                    variant="ghost"
                                    size="xs"
                                    @click="deleteOrganization(getOrg(row))"
                                />
                            </UTooltip>
                        </div>
                        <NuxtLink v-else :to="`/admin/organizations/${row.original.id}`" class="view-link">
                            View
                        </NuxtLink>
                    </template>
                </UTable>

                <!-- Pagination -->
                <div v-if="totalPages > 1" class="pagination-footer">
                    <div class="pagination-info">
                        Showing {{ (page - 1) * limit + 1 }}-{{ Math.min(page * limit, orgsData?.total ?? 0) }} of
                        {{ orgsData?.total ?? 0 }}
                    </div>
                    <UPagination v-model="page" :total="orgsData?.total ?? 0" :items-per-page="limit" />
                </div>
            </UCard>

            <!-- Create Organization Modal -->
            <OrganizationsCreateModal
                v-model:open="showCreateModal"
                :is-creating="isCreating"
                @create="createOrganization"
            />
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.admin-orgs {
    @apply max-w-7xl mx-auto;
}

.page-header {
    @apply flex items-center justify-between mb-6;
}

.header-left {
    @apply flex items-baseline gap-4;
}

.page-title {
    @apply text-2xl font-semibold text-gray-900 dark:text-gray-100;
}

.org-count {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.filters {
    @apply flex items-end gap-4 mb-4 flex-wrap relative z-10;
}

.search-input {
    @apply w-64;
}

.filter-item {
    @apply flex flex-col gap-1;
}

.filter-label {
    @apply text-xs font-medium text-gray-500 dark:text-gray-400;
}

.org-link {
    @apply text-primary-500 no-underline;
}

.org-link:hover {
    @apply underline;
}

.member-info {
    @apply flex flex-col gap-0.5 text-sm;
}

.quota-info {
    @apply text-xs text-gray-500 dark:text-gray-400;
}

.over-quota {
    @apply text-xs text-red-600 dark:text-red-400 font-medium;
}

.actions {
    @apply flex gap-1;
}

.status-badges {
    @apply flex flex-wrap gap-1;
}

.view-link {
    @apply text-sm text-gray-500 dark:text-gray-400 hover:underline;
}

.pagination-footer {
    @apply flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700;
}

.pagination-info {
    @apply text-sm text-gray-500 dark:text-gray-400;
}
</style>
