<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    layout: 'admin',
    middleware: ['admin'],
});

const api = useApi();
const toast = useToast();
const modal = useModalStore();

const search = ref('');
const searchDebounced = refDebounced(search, 300);

// Filters
const isAdminFilter = ref('all');
const isPremiumFilter = ref('all');

const filterOptions = [
    { label: 'All', value: 'all' },
    { label: 'Yes', value: 'yes' },
    { label: 'No', value: 'no' },
];

function filterToBool(value: string): boolean | undefined {
    if (value === 'yes') return true;
    if (value === 'no') return false;
    return undefined;
}

// Pagination
const page = ref(1);
const itemsPerPage = 100;

// Reset page when filters change
watch([searchDebounced, isAdminFilter, isPremiumFilter], () => {
    page.value = 1;
});

const {
    data: usersData,
    pending,
    refresh,
} = await useAsyncData<AdminUserListResponse>(
    'admin-users',
    () => api.get('/admin/users', {
        search: searchDebounced.value || undefined,
        is_admin: filterToBool(isAdminFilter.value),
        is_premium: filterToBool(isPremiumFilter.value),
        limit: itemsPerPage,
        offset: (page.value - 1) * itemsPerPage,
    }),
    { watch: [searchDebounced, isAdminFilter, isPremiumFilter, page], server: false },
);

const totalPages = computed(() => Math.ceil((usersData.value?.total ?? 0) / itemsPerPage));

// Table columns configuration
const columns = [
    { accessorKey: 'id', header: 'ID' },
    { accessorKey: 'email', header: 'Email' },
    { accessorKey: 'name', header: 'Name' },
    { accessorKey: 'is_admin', header: 'Admin' },
    { accessorKey: 'is_premium', header: 'Premium' },
    { accessorKey: 'created_at', header: 'Created' },
    { accessorKey: 'actions', header: 'Actions' },
];

function formatDate(dateStr: string | null): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
}

async function impersonateUser(user: AdminUserRead) {
    try {
        const response = await api.post<ImpersonationResponse>(`/admin/impersonate/${user.id}`);

        // Get the auth store
        const auth = useAuth();

        // Save the new impersonation token
        auth.saveUserToken({
            access_token: response.access_token,
            token_parsed: response.token_parsed,
            user: response.user,
            token_type: 'bearer',
        });

        toast.add({
            title: 'Impersonation started',
            description: `Now viewing as ${user.email}`,
            color: 'success',
            duration: 3000,
        });

        // Navigate to home to experience as user
        await navigateTo('/');
    } catch (error) {
        toast.add({
            title: 'Error',
            description: 'Failed to start impersonation',
            color: 'error',
            duration: 3000,
        });
    }
}

async function deleteUser(user: AdminUserRead) {
    const confirmed = await modal.open('confirm', {
        title: 'Delete User',
        message: `Are you sure you want to delete ${user.email}? This action cannot be undone.`,
        confirmText: 'Delete',
        confirmColor: 'error',
    });

    if (!confirmed) return;

    try {
        await api.delete(`/admin/users/${user.id}`);
        toast.add({
            title: 'User deleted',
            description: `${user.email} has been deleted`,
            color: 'success',
            duration: 3000,
        });
        refresh();
    } catch (error) {
        toast.add({
            title: 'Error',
            description: 'Failed to delete user',
            color: 'error',
            duration: 3000,
        });
    }
}
</script>

<template>
    <div class="admin-users">
        <div class="page-header">
            <h1 class="page-title">Users</h1>
            <span class="user-count">{{ usersData?.total ?? 0 }} total</span>
        </div>

        <!-- Filters -->
        <div class="filters">
            <UInput
                v-model="search"
                placeholder="Search by email or name..."
                icon="i-lucide-search"
                class="search-input"
            />
            <div class="filter-item">
                <label class="filter-label">Admin</label>
                <USelect
                    v-model="isAdminFilter"
                    :items="filterOptions"
                    class="w-24"
                />
            </div>
            <div class="filter-item">
                <label class="filter-label">Premium</label>
                <USelect
                    v-model="isPremiumFilter"
                    :items="filterOptions"
                    class="w-24"
                />
            </div>
        </div>

        <!-- Users Table -->
        <UCard :ui="{ body: 'p-0 sm:p-0' }">
            <UTable
                :columns="columns"
                :data="usersData?.items ?? []"
                :loading="pending"
            >
                <template #email-cell="{ row }">
                    <NuxtLink :to="`/admin/users/${row.original.id}`" class="user-link">
                        {{ row.original.email }}
                    </NuxtLink>
                </template>

                <template #name-cell="{ row }">
                    {{ row.original.first_name }} {{ row.original.last_name }}
                </template>

                <template #is_admin-cell="{ row }">
                    <UBadge v-if="row.original.is_admin" label="Admin" color="info" />
                </template>

                <template #is_premium-cell="{ row }">
                    <UBadge v-if="row.original.is_premium" label="Premium" color="warning" />
                </template>

                <template #created_at-cell="{ row }">
                    {{ formatDate(row.original.created_at) }}
                </template>

                <template #actions-cell="{ row }">
                    <div class="actions">
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
                                <UButton
                                    icon="i-lucide-pencil"
                                    color="neutral"
                                    variant="ghost"
                                    size="xs"
                                />
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
                </template>
            </UTable>

            <!-- Pagination -->
            <div v-if="totalPages > 1" class="pagination-footer">
                <div class="pagination-info">
                    Showing {{ (page - 1) * itemsPerPage + 1 }}-{{ Math.min(page * itemsPerPage, usersData?.total ?? 0) }}
                    of {{ usersData?.total ?? 0 }}
                </div>
                <UPagination v-model="page" :total="usersData?.total ?? 0" :items-per-page="itemsPerPage" />
            </div>
        </UCard>
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

.pagination-footer {
    @apply flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700;
}

.pagination-info {
    @apply text-sm text-gray-500 dark:text-gray-400;
}
</style>
