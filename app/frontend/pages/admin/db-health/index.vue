<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin'],
});

const api = useApi();

const { data, pending, refresh } = await useAsyncData<DatabaseHealthResponse>(
    'admin-db-health',
    () => api.get('/admin/db-health'),
    { server: false },
);

// Tab state
const activeTab = ref<'tables' | 'indexes'>('tables');

// Table columns
const tableColumns = [
    { accessorKey: 'name', header: 'Table' },
    { accessorKey: 'size_pretty', header: 'Size' },
    { accessorKey: 'row_count', header: 'Rows' },
    { accessorKey: 'dead_tuples', header: 'Dead Tuples' },
    { accessorKey: 'seq_scans', header: 'Seq Scans' },
    { accessorKey: 'idx_scans', header: 'Idx Scans' },
    { accessorKey: 'last_vacuum', header: 'Last Vacuum' },
];

const indexColumns = [
    { accessorKey: 'name', header: 'Index' },
    { accessorKey: 'table', header: 'Table' },
    { accessorKey: 'size_pretty', header: 'Size' },
    { accessorKey: 'scans', header: 'Scans' },
    { accessorKey: 'is_unused', header: 'Status' },
];

function formatDate(dateStr: string | null): string {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
}

function getHealthColor(
    ratio: number,
    thresholdWarning: number,
    thresholdCritical: number,
): 'success' | 'warning' | 'error' {
    if (ratio >= thresholdWarning) return 'success';
    if (ratio >= thresholdCritical) return 'warning';
    return 'error';
}

function getCacheColor(ratio: number): 'success' | 'warning' | 'error' {
    return getHealthColor(ratio, 95, 90);
}

function getConnectionColor(active: number, max: number): 'success' | 'warning' | 'error' {
    const ratio = (1 - active / max) * 100;
    return getHealthColor(ratio, 20, 10);
}

function getSeverityColor(severity: string): 'info' | 'warning' | 'error' | 'success' {
    switch (severity) {
        case 'critical':
            return 'error';
        case 'warning':
            return 'warning';
        case 'info':
        default:
            return 'info';
    }
}

function getSeverityIcon(severity: string): string {
    switch (severity) {
        case 'critical':
            return 'i-lucide-alert-circle';
        case 'warning':
            return 'i-lucide-alert-triangle';
        case 'info':
        default:
            return 'i-lucide-info';
    }
}
</script>

<template>
    <div class="page-box">
        <UiPageTitleBanner>
            Admin
            <template #subtitle> Manage users, organizations, and system settings </template>
            <template #subnav>
                <AdminSubnav />
            </template>
        </UiPageTitleBanner>

        <div class="admin-db-health">
            <div class="page-header">
                <h1 class="page-title">Database Health</h1>
                <UButton
                    icon="i-lucide-refresh-cw"
                    label="Refresh"
                    color="neutral"
                    variant="outline"
                    :loading="pending"
                    @click="() => refresh()"
                />
            </div>

            <!-- Summary Cards -->
            <div class="stats-grid">
                <UCard class="stat-card">
                    <div class="stat-label">Database Size</div>
                    <div class="stat-value">{{ data?.database_size_pretty ?? '-' }}</div>
                    <UBadge color="success" variant="subtle" class="stat-badge">
                        <UIcon name="i-lucide-check-circle" class="mr-1" />
                        OK
                    </UBadge>
                </UCard>

                <UCard class="stat-card">
                    <div class="stat-label">Connections</div>
                    <div class="stat-value">{{ data?.active_connections ?? 0 }} / {{ data?.max_connections ?? 0 }}</div>
                    <UBadge
                        :color="data ? getConnectionColor(data.active_connections, data.max_connections) : 'neutral'"
                        variant="subtle"
                        class="stat-badge"
                    >
                        <UIcon name="i-lucide-check-circle" class="mr-1" />
                        {{ data ? ((data.active_connections / data.max_connections) * 100).toFixed(0) : 0 }}% used
                    </UBadge>
                </UCard>

                <UCard class="stat-card">
                    <div class="stat-label">Cache Hit Ratio</div>
                    <div class="stat-value">{{ data?.cache_hit_ratio?.toFixed(1) ?? '-' }}%</div>
                    <UBadge
                        :color="data ? getCacheColor(data.cache_hit_ratio) : 'neutral'"
                        variant="subtle"
                        class="stat-badge"
                    >
                        <UIcon
                            :name="
                                data && data.cache_hit_ratio >= 95 ? 'i-lucide-check-circle' : 'i-lucide-alert-triangle'
                            "
                            class="mr-1"
                        />
                        {{ data && data.cache_hit_ratio >= 95 ? 'Healthy' : 'Needs attention' }}
                    </UBadge>
                </UCard>

                <UCard class="stat-card">
                    <div class="stat-label">Tables</div>
                    <div class="stat-value">{{ data?.tables?.length ?? 0 }}</div>
                    <UBadge color="neutral" variant="subtle" class="stat-badge">
                        {{ data?.indexes?.length ?? 0 }} indexes
                    </UBadge>
                </UCard>
            </div>

            <!-- Recommendations -->
            <UCard v-if="data?.recommendations?.length" class="recommendations-card">
                <template #header>
                    <h2 class="section-title">Recommendations ({{ data.recommendations.length }})</h2>
                </template>
                <div class="recommendations-list">
                    <div v-for="(rec, index) in data.recommendations" :key="index" class="recommendation-item">
                        <UBadge :color="getSeverityColor(rec.severity)" variant="subtle" size="xs">
                            {{ rec.severity }}
                        </UBadge>
                        <span v-if="rec.table" class="recommendation-table">{{ rec.table }}:</span>
                        <span class="recommendation-message">{{ rec.action }}</span>
                    </div>
                </div>
            </UCard>

            <!-- Tabs for Tables and Indexes -->
            <div class="tabs-container">
                <div class="tabs">
                    <button :class="['tab', { active: activeTab === 'tables' }]" @click="activeTab = 'tables'">
                        Tables
                    </button>
                    <button :class="['tab', { active: activeTab === 'indexes' }]" @click="activeTab = 'indexes'">
                        Indexes
                    </button>
                </div>

                <!-- Tables Tab -->
                <UCard v-if="activeTab === 'tables'">
                    <UTable :columns="tableColumns" :data="data?.tables ?? []" :loading="pending">
                        <template #row_count-cell="{ row }">
                            {{ row.original.row_count.toLocaleString() }}
                        </template>
                        <template #dead_tuples-cell="{ row }">
                            <span :class="{ 'text-warning': row.original.dead_tuples > row.original.row_count * 0.1 }">
                                {{ row.original.dead_tuples.toLocaleString() }}
                            </span>
                        </template>
                        <template #seq_scans-cell="{ row }">
                            {{ row.original.seq_scans.toLocaleString() }}
                        </template>
                        <template #idx_scans-cell="{ row }">
                            {{ row.original.idx_scans.toLocaleString() }}
                        </template>
                        <template #last_vacuum-cell="{ row }">
                            {{ formatDate(row.original.last_vacuum) }}
                        </template>
                    </UTable>
                </UCard>

                <!-- Indexes Tab -->
                <UCard v-if="activeTab === 'indexes'">
                    <UTable :columns="indexColumns" :data="data?.indexes ?? []" :loading="pending">
                        <template #scans-cell="{ row }">
                            {{ row.original.scans.toLocaleString() }}
                        </template>
                        <template #is_unused-cell="{ row }">
                            <UBadge
                                :color="row.original.is_unused ? 'warning' : 'success'"
                                :label="row.original.is_unused ? 'Unused' : 'Active'"
                                variant="subtle"
                            />
                        </template>
                    </UTable>
                </UCard>
            </div>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.admin-db-health {
    @apply max-w-7xl mx-auto;
}

.page-header {
    @apply flex items-center justify-between mb-6;
}

.page-title {
    @apply text-2xl font-semibold text-gray-900 dark:text-gray-100;
}

.stats-grid {
    @apply grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6;
}

.stat-card {
    @apply text-center;
}

.stat-label {
    @apply text-sm text-gray-500 dark:text-gray-400 mb-1;
}

.stat-value {
    @apply text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2;
}

.stat-badge {
    @apply inline-flex items-center;
}

.section-title {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100;
}

.recommendations-card {
    @apply mb-6;
}

.recommendations-list {
    @apply space-y-2 max-h-[200px] overflow-y-auto;
}

.recommendation-item {
    @apply flex items-center gap-2 text-sm;
}

.recommendation-table {
    @apply font-mono text-gray-500 dark:text-gray-400;
}

.recommendation-message {
    @apply text-gray-700 dark:text-gray-300;
}

.tabs-container {
    @apply space-y-4;
}

.tabs {
    @apply flex gap-2;
}

.tab {
    @apply px-4 py-2 text-sm font-medium rounded-lg transition-colors;
    @apply text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100;
    @apply hover:bg-gray-100 dark:hover:bg-gray-800;
}

.tab.active {
    @apply bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300;
}

.text-warning {
    @apply text-amber-600 dark:text-amber-400 font-medium;
}
</style>
