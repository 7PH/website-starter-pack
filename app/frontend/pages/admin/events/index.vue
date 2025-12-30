<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    layout: 'admin',
    middleware: ['admin'],
});

const api = useApi();

// Filters
const actionFilter = ref('all');
const userIdFilter = ref<string>('');
const fromDateStr = ref<string>('');
const toDateStr = ref<string>('');

// Convert string to Date for API
const fromDate = computed(() => fromDateStr.value ? new Date(fromDateStr.value) : null);
const toDate = computed(() => toDateStr.value ? new Date(toDateStr.value) : null);

// Action categories for filter dropdown
const actionCategories = [
    { label: 'All Events', value: 'all' },
    { label: 'User Events', value: 'user.' },
    { label: 'Admin Events', value: 'admin.' },
];

// Table columns
const columns = [
    { accessorKey: 'id', header: 'ID' },
    { accessorKey: 'action', header: 'Action' },
    { accessorKey: 'user_id', header: 'User' },
    { accessorKey: 'ip_address', header: 'IP' },
    { accessorKey: 'created_at', header: 'Time' },
    { accessorKey: 'details', header: 'Details' },
];

const {
    data: eventsData,
    pending,
    refresh,
} = await useAsyncData<EventLogListResponse>(
    'admin-events',
    () =>
        api.get('/admin/events', {
            action_prefix: actionFilter.value === 'all' ? undefined : actionFilter.value,
            user_id: userIdFilter.value ? Number(userIdFilter.value) : undefined,
            from_date: fromDate.value?.toISOString() || undefined,
            to_date: toDate.value?.toISOString() || undefined,
            limit: 100,
        }),
    { watch: [actionFilter, userIdFilter, fromDate, toDate], server: false },
);

function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString();
}

function formatAction(action: string): string {
    return action
        .split('.')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
}

function getActionColor(action: string): 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral' {
    if (action.startsWith('admin.')) return 'info';
    if (action.startsWith('user.login') || action.startsWith('user.register')) return 'success';
    if (action.includes('delete')) return 'error';
    return 'neutral';
}

function clearFilters() {
    actionFilter.value = null;
    userIdFilter.value = '';
    fromDateStr.value = '';
    toDateStr.value = '';
}
</script>

<template>
    <div class="admin-events">
        <h1 class="page-title">Event Logs</h1>

        <!-- Filters -->
        <UCard class="filters-card mb-4">
            <div class="filters">
                <div class="filter-item">
                    <label class="filter-label">Event Type</label>
                    <USelect
                        v-model="actionFilter"
                        :items="actionCategories"
                        placeholder="All Events"
                        class="w-40"
                    />
                </div>
                <div class="filter-item">
                    <label class="filter-label">User ID</label>
                    <UInput
                        v-model="userIdFilter"
                        type="number"
                        placeholder="User ID"
                        class="w-28"
                    />
                </div>
                <div class="filter-item">
                    <label class="filter-label">From Date</label>
                    <UInput
                        v-model="fromDateStr"
                        type="datetime-local"
                        class="w-48"
                    />
                </div>
                <div class="filter-item">
                    <label class="filter-label">To Date</label>
                    <UInput
                        v-model="toDateStr"
                        type="datetime-local"
                        class="w-48"
                    />
                </div>
                <div class="filter-actions">
                    <UButton label="Clear" color="neutral" variant="outline" size="sm" @click="clearFilters" />
                    <UTooltip text="Refresh">
                        <UButton
                            icon="i-lucide-refresh-cw"
                            color="neutral"
                            variant="outline"
                            size="sm"
                            @click="() => refresh()"
                        />
                    </UTooltip>
                </div>
            </div>
        </UCard>

        <!-- Events Table -->
        <UCard>
            <UTable
                :columns="columns"
                :data="eventsData?.items ?? []"
                :loading="pending"
                class="max-h-[calc(100vh-20rem)] overflow-auto"
            >
                <template #action-cell="{ row }">
                    <UBadge :label="formatAction(row.original.action)" :color="getActionColor(row.original.action)" />
                </template>

                <template #user_id-cell="{ row }">
                    <NuxtLink v-if="row.original.user_id" :to="`/admin/users/${row.original.user_id}`" class="user-link">
                        #{{ row.original.user_id }}
                    </NuxtLink>
                    <span v-else class="text-muted">-</span>
                </template>

                <template #ip_address-cell="{ row }">
                    <code v-if="row.original.ip_address" class="ip-code">{{ row.original.ip_address }}</code>
                    <span v-else class="text-muted">-</span>
                </template>

                <template #created_at-cell="{ row }">
                    {{ formatDate(row.original.created_at) }}
                </template>

                <template #details-cell="{ row }">
                    <code v-if="Object.keys(row.original.details).length > 0" class="details-code">
                        {{ JSON.stringify(row.original.details) }}
                    </code>
                    <span v-else class="text-muted">-</span>
                </template>
            </UTable>

            <div class="table-footer">
                <span class="total-count">{{ eventsData?.total ?? 0 }} events</span>
            </div>
        </UCard>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.admin-events {
    @apply max-w-7xl mx-auto;
}

.page-title {
    @apply text-2xl font-semibold mb-6 text-gray-900 dark:text-gray-100;
}

.filters {
    @apply flex items-end gap-4 flex-wrap;
}

.filter-item {
    @apply flex flex-col gap-2 flex-shrink-0;
}

.filter-label {
    @apply text-xs font-medium text-gray-500 dark:text-gray-400;
}

.filter-actions {
    @apply flex gap-2 ml-auto;
}

.user-link {
    @apply text-primary-500 no-underline;
}

.user-link:hover {
    @apply underline;
}

.text-muted {
    @apply text-gray-500 dark:text-gray-400;
}

.ip-code {
    @apply text-xs bg-gray-100 dark:bg-gray-700 py-0.5 px-1.5 rounded;
}

.details-code {
    @apply text-xs bg-gray-100 dark:bg-gray-700 py-1 px-2 rounded max-w-xs break-all whitespace-pre-wrap inline-block;
}

.table-footer {
    @apply flex justify-end pt-4;
}

.total-count {
    @apply text-sm text-gray-500 dark:text-gray-400;
}
</style>
