<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    layout: 'admin',
    middleware: ['admin'],
});

import { formatDate } from '~/utils/formatters';
import { getErrorMessage } from '~/utils/errors';

// Types from models.ts are declared globally

const api = useApi();
const toast = useToast();
const modal = useModalStore();

const search = ref('');
const searchDebounced = refDebounced(search, 300);

// Filters
const premiumFilter = ref('all');
const deletedFilter = ref('hide');

const filterOptions = [
    { label: 'All', value: 'all' },
    { label: 'Yes', value: 'yes' },
    { label: 'No', value: 'no' },
];

const deletedFilterOptions = [
    { label: 'Hide deleted', value: 'hide' },
    { label: 'Show all', value: 'all' },
    { label: 'Only deleted', value: 'only' },
];

function filterToBool(value: string): boolean | undefined {
    if (value === 'yes') return true;
    if (value === 'no') return false;
    return undefined;
}

// Pagination
const page = ref(1);
const ITEMS_PER_PAGE = 100;

// Reset page when filters change
watch([searchDebounced, premiumFilter, deletedFilter], () => {
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
            stripe_premium: filterToBool(premiumFilter.value),
            include_deleted: deletedFilter.value !== 'hide' ? true : undefined,
            only_deleted: deletedFilter.value === 'only' ? true : undefined,
            limit: ITEMS_PER_PAGE,
            offset: (page.value - 1) * ITEMS_PER_PAGE,
        }),
    { watch: [searchDebounced, premiumFilter, deletedFilter, page], server: false },
);

const totalPages = computed(() => Math.ceil((orgsData.value?.total ?? 0) / ITEMS_PER_PAGE));

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
const createForm = ref({
    name: '',
    email: '',
    description: '',
});
const isCreating = ref(false);

async function createOrganization() {
    isCreating.value = true;
    try {
        await api.post('/organizations', createForm.value);
        toast.add({
            title: 'Organization created',
            description: `${createForm.value.name} has been created`,
            color: 'success',
            duration: 3000,
        });
        showCreateModal.value = false;
        createForm.value = { name: '', email: '', description: '' };
        refresh();
    } catch (error: unknown) {
        toast.add({
            title: 'Error',
            description: getErrorMessage(error, 'Failed to create organization'),
            color: 'error',
            duration: 3000,
        });
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
        toast.add({
            title: 'Organization deleted',
            description: `${org.name} has been deleted`,
            color: 'success',
            duration: 3000,
        });
        refresh();
    } catch (error: unknown) {
        toast.add({
            title: 'Error',
            description: getErrorMessage(error, 'Failed to delete organization'),
            color: 'error',
            duration: 3000,
        });
    }
}
</script>

<template>
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
                <USelect v-model="premiumFilter" :items="filterOptions" class="w-24" />
            </div>
            <div class="filter-item">
                <label class="filter-label">Deleted</label>
                <USelect v-model="deletedFilter" :items="deletedFilterOptions" class="w-32" />
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
                    <NuxtLink v-else :to="`/admin/organizations/${row.original.id}`" class="view-link"> View </NuxtLink>
                </template>
            </UTable>

            <!-- Pagination -->
            <div v-if="totalPages > 1" class="pagination-footer">
                <div class="pagination-info">
                    Showing {{ (page - 1) * ITEMS_PER_PAGE + 1 }}-{{
                        Math.min(page * ITEMS_PER_PAGE, orgsData?.total ?? 0)
                    }}
                    of {{ orgsData?.total ?? 0 }}
                </div>
                <UPagination v-model="page" :total="orgsData?.total ?? 0" :items-per-page="ITEMS_PER_PAGE" />
            </div>
        </UCard>

        <!-- Create Organization Modal -->
        <UModal v-model:open="showCreateModal">
            <template #content>
                <UCard>
                    <template #header>
                        <UiModalHeader title="Create Organization" @close="showCreateModal = false" />
                    </template>

                    <form class="create-form" @submit.prevent="createOrganization">
                        <UFormField label="Name" required>
                            <UInput v-model="createForm.name" placeholder="Organization name" />
                        </UFormField>
                        <UFormField label="Email" required>
                            <UInput v-model="createForm.email" type="email" placeholder="contact@example.com" />
                        </UFormField>
                        <UFormField label="Description">
                            <UTextarea
                                v-model="createForm.description"
                                placeholder="Optional description..."
                                :rows="3"
                            />
                        </UFormField>
                        <UiFormActions>
                            <UButton
                                label="Cancel"
                                color="neutral"
                                variant="outline"
                                @click="showCreateModal = false"
                            />
                            <UButton
                                type="submit"
                                label="Create"
                                :loading="isCreating"
                                :disabled="!createForm.name || !createForm.email"
                            />
                        </UiFormActions>
                    </form>
                </UCard>
            </template>
        </UModal>
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

.create-form {
    @apply flex flex-col gap-4;
}
</style>
