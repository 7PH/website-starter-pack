<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatDate } from '~/utils/formatters';
import { DELETED_FILTER_OPTIONS, YES_NO_FILTER_OPTIONS, yesNoToBool } from '~/utils/admin-filters';

definePageMeta({
    middleware: ['admin'],
});

const api = useApi();
const { showSuccess, showError } = useToastHelpers();
const modal = useModalStore();
const { impersonate } = useAdminImpersonation();

const { search, debouncedSearch: searchDebounced, page, limit, offset } = useTableState({ defaultLimit: 100 });

// Filters
const isAdminFilter = ref('all');
const isPremiumFilter = ref('all');
const deletedFilter = ref('hide');

// useTableState resets page on debouncedSearch; reset on other filters too.
watch([isAdminFilter, isPremiumFilter, deletedFilter], () => {
    page.value = 1;
});

const {
    data: usersData,
    pending,
    refresh,
} = await useAsyncData<AdminUserListResponse>(
    'admin-users',
    () =>
        api.get('/admin/users', {
            search: searchDebounced.value || undefined,
            is_admin: yesNoToBool(isAdminFilter.value),
            is_premium: yesNoToBool(isPremiumFilter.value),
            include_deleted: deletedFilter.value !== 'hide' ? true : undefined,
            only_deleted: deletedFilter.value === 'only' ? true : undefined,
            limit: limit.value,
            offset: offset.value,
        }),
    { watch: [searchDebounced, isAdminFilter, isPremiumFilter, deletedFilter, page], server: false },
);

const totalPages = computed(() => Math.ceil((usersData.value?.total ?? 0) / limit.value));

// Table columns configuration
const columns = [
    { accessorKey: 'id', header: 'ID' },
    { accessorKey: 'email', header: 'Email' },
    { accessorKey: 'name', header: 'Name' },
    { accessorKey: 'status', header: 'Status' },
    { accessorKey: 'created_at', header: 'Created' },
    { accessorKey: 'actions', header: 'Actions' },
];

function nameLabel(user: AdminUserRead): string {
    return user.display_label ?? `User #${user.id}`;
}

const AUTH_BADGE: Record<string, { label: string; color: 'info' | 'warning' | 'neutral' }> = {
    oauth: { label: 'OAuth', color: 'info' },
    access_code: { label: 'Code', color: 'warning' },
    deleted: { label: 'Deleted', color: 'neutral' },
};

function authBadge(method: string | undefined | null) {
    return method ? AUTH_BADGE[method] : undefined;
}

function impersonateUser(user: AdminUserRead) {
    return impersonate(user.id, nameLabel(user));
}

async function deleteUser(user: AdminUserRead) {
    const label = nameLabel(user);
    const confirmed = await modal.open('confirm', {
        title: 'Delete User',
        message: `Are you sure you want to delete ${label}? This action cannot be undone.`,
        confirmText: 'Delete',
        confirmColor: 'error',
    });

    if (!confirmed) return;

    try {
        await api.delete(`/admin/users/${user.id}`);
        showSuccess('User deleted', `${label} has been deleted`);
        refresh();
    } catch (error) {
        showError(error, 'core.errors.generic');
    }
}
</script>

<template>
    <div class="page-box">
        <AdminPageBanner />

        <div class="admin-users">
            <div class="page-header">
                <h1 class="page-title">Users</h1>
                <span class="user-count">{{ usersData?.total ?? 0 }} total</span>
            </div>

            <!-- Filters -->
            <div class="filters">
                <UInput
                    v-model="search"
                    placeholder="Search by id, email or name..."
                    icon="i-lucide-search"
                    class="search-input"
                />
                <div class="filter-item">
                    <label class="filter-label">Admin</label>
                    <USelect v-model="isAdminFilter" :items="YES_NO_FILTER_OPTIONS" class="w-24" />
                </div>
                <div class="filter-item">
                    <label class="filter-label">Premium</label>
                    <USelect v-model="isPremiumFilter" :items="YES_NO_FILTER_OPTIONS" class="w-24" />
                </div>
                <div class="filter-item">
                    <label class="filter-label">Deleted</label>
                    <USelect v-model="deletedFilter" :items="DELETED_FILTER_OPTIONS" class="w-32" />
                </div>
            </div>

            <!-- Users Table -->
            <UCard :ui="{ body: 'p-0 sm:p-0' }">
                <UTable :columns="columns" :data="usersData?.items ?? []" :loading="pending">
                    <template #email-cell="{ row }">
                        <NuxtLink :to="`/admin/users/${row.original.id}`" class="user-link">
                            {{ row.original.email ?? '—' }}
                        </NuxtLink>
                    </template>

                    <template #name-cell="{ row }">
                        <NuxtLink :to="`/admin/users/${row.original.id}`" class="user-link">
                            {{ nameLabel(row.original as AdminUserRead) }}
                        </NuxtLink>
                    </template>

                    <template #status-cell="{ row }">
                        <div class="status-badges">
                            <UBadge v-if="row.original.deleted_at" label="Deleted" color="error" />
                            <UBadge v-if="row.original.is_admin" label="Admin" color="info" />
                            <UBadge v-if="row.original.is_premium" label="Premium" color="warning" />
                            <template v-if="authBadge(row.original.auth_method)">
                                <UBadge
                                    :label="authBadge(row.original.auth_method)!.label"
                                    :color="authBadge(row.original.auth_method)!.color"
                                    variant="soft"
                                />
                            </template>
                        </div>
                    </template>

                    <template #created_at-cell="{ row }">
                        {{ formatDate(row.original.created_at) }}
                    </template>

                    <template #actions-cell="{ row }">
                        <div v-if="!row.original.deleted_at" class="actions">
                            <UTooltip text="Impersonate">
                                <UButton
                                    icon="i-lucide-user"
                                    color="neutral"
                                    variant="ghost"
                                    size="xs"
                                    @click="impersonateUser(row.original as AdminUserRead)"
                                />
                            </UTooltip>
                            <UTooltip text="Edit">
                                <NuxtLink :to="`/admin/users/${row.original.id}`">
                                    <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" size="xs" />
                                </NuxtLink>
                            </UTooltip>
                            <UTooltip text="Delete">
                                <UButton
                                    icon="i-lucide-trash-2"
                                    color="error"
                                    variant="ghost"
                                    size="xs"
                                    @click="deleteUser(row.original as AdminUserRead)"
                                />
                            </UTooltip>
                        </div>
                        <NuxtLink v-else :to="`/admin/users/${row.original.id}`" class="view-link"> View </NuxtLink>
                    </template>
                </UTable>

                <!-- Pagination -->
                <div v-if="totalPages > 1" class="pagination-footer">
                    <div class="pagination-info">
                        Showing {{ (page - 1) * limit + 1 }}-{{ Math.min(page * limit, usersData?.total ?? 0) }} of
                        {{ usersData?.total ?? 0 }}
                    </div>
                    <UPagination v-model="page" :total="usersData?.total ?? 0" :items-per-page="limit" />
                </div>
            </UCard>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.admin-users {
    @apply max-w-7xl mx-auto;
}

.page-header {
    @apply flex items-baseline gap-4 mb-6;
}

.page-title {
    @apply text-2xl font-semibold text-gray-900 dark:text-gray-100;
}

.user-count {
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

.user-link {
    @apply text-primary-500 no-underline;
}

.user-link:hover {
    @apply underline;
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
