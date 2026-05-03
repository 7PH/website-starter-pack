<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin'],
});

const backendConfig = useBackendConfig();

// Keys declared in CoreBackendConfig (app/backend/src/schemas/config.py).
// Anything else returned by /config is treated as a sub-app extension.
const CORE_KEYS = new Set<string>([
    'password_min_length',
    'org_max_per_user',
    'org_max_members',
    'org_invitation_expiry_days',
    'managed_account_group_max_per_user',
    'managed_accounts_max_per_user',
    'stripe_enabled',
    'organizations_enabled',
    'org_invitations_enabled',
    'managed_accounts_enabled',
    'llm_enabled',
    'org_self_service_subscriptions',
    'org_self_service_creation',
    'llm_provider',
    'llm_model',
]);

interface ConfigEntry {
    key: string;
    value: unknown;
    type: string;
}

function partition(cfg: Record<string, unknown> | null): { core: ConfigEntry[]; extra: ConfigEntry[] } {
    if (!cfg) return { core: [], extra: [] };
    const core: ConfigEntry[] = [];
    const extra: ConfigEntry[] = [];
    for (const key of Object.keys(cfg).sort()) {
        const entry: ConfigEntry = { key, value: cfg[key], type: typeof cfg[key] };
        (CORE_KEYS.has(key) ? core : extra).push(entry);
    }
    return { core, extra };
}

const partitioned = computed(() => partition(backendConfig.config as Record<string, unknown> | null));

const columns = [
    { accessorKey: 'key', header: 'Key' },
    { accessorKey: 'value', header: 'Value' },
    { accessorKey: 'type', header: 'Type' },
];
</script>

<template>
    <div class="page-box">
        <AdminPageBanner />

        <div class="admin-config">
            <div class="page-header">
                <h1 class="page-title">Configuration</h1>
                <span class="page-subtitle">Public config served by /api/v1/config — what the frontend sees.</span>
            </div>

            <UCard v-if="!backendConfig.config" class="error-card">
                <div class="error-content">
                    <UIcon name="i-lucide-alert-triangle" class="error-icon" />
                    <span>Failed to load config from /api/v1/config.</span>
                </div>
            </UCard>

            <template v-else>
                <UCard class="config-section">
                    <template #header>
                        <h2 class="section-title">Core</h2>
                    </template>
                    <UTable :columns="columns" :data="partitioned.core" :ui="{ td: 'align-top' }">
                        <template #key-cell="{ row }">
                            <span class="key-cell">{{ row.original.key }}</span>
                        </template>
                        <template #value-cell="{ row }">
                            <UBadge
                                v-if="row.original.type === 'boolean'"
                                :color="row.original.value ? 'success' : 'neutral'"
                                :label="row.original.value ? 'Enabled' : 'Disabled'"
                                variant="subtle"
                            />
                            <span v-else-if="row.original.value === ''" class="empty-value">(empty)</span>
                            <span v-else-if="row.original.value === null || row.original.value === undefined">—</span>
                            <span v-else class="number-value">{{ row.original.value }}</span>
                        </template>
                        <template #type-cell="{ row }">
                            <span class="type-cell">{{ row.original.type }}</span>
                        </template>
                    </UTable>
                </UCard>

                <UCard class="config-section">
                    <template #header>
                        <h2 class="section-title">Sub-app extensions</h2>
                    </template>
                    <UTable
                        v-if="partitioned.extra.length"
                        :columns="columns"
                        :data="partitioned.extra"
                        :ui="{ td: 'align-top' }"
                    >
                        <template #key-cell="{ row }">
                            <span class="key-cell">{{ row.original.key }}</span>
                        </template>
                        <template #value-cell="{ row }">
                            <UBadge
                                v-if="row.original.type === 'boolean'"
                                :color="row.original.value ? 'success' : 'neutral'"
                                :label="row.original.value ? 'Enabled' : 'Disabled'"
                                variant="subtle"
                            />
                            <span v-else-if="row.original.value === ''" class="empty-value">(empty)</span>
                            <span v-else-if="row.original.value === null || row.original.value === undefined">—</span>
                            <span v-else class="number-value">{{ row.original.value }}</span>
                        </template>
                        <template #type-cell="{ row }">
                            <span class="type-cell">{{ row.original.type }}</span>
                        </template>
                    </UTable>
                    <div v-else class="empty-hint">
                        No project-specific config. Add fields by editing
                        <code>app/backend/src/schemas/config_ext.py</code> and returning them from
                        <code>build_extra()</code>.
                    </div>
                </UCard>
            </template>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.admin-config {
    @apply max-w-5xl mx-auto;
}

.page-header {
    @apply flex flex-col gap-1 mb-6;
}

.page-title {
    @apply text-2xl font-semibold text-gray-900 dark:text-gray-100;
}

.page-subtitle {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.section-title {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100;
}

.config-section {
    @apply mb-6;
}

.key-cell {
    @apply font-mono text-sm text-gray-900 dark:text-gray-100;
}

.type-cell {
    @apply font-mono text-xs text-gray-500 dark:text-gray-400;
}

.number-value {
    @apply font-mono text-sm;
}

.empty-value {
    @apply italic text-gray-500 dark:text-gray-400;
}

.empty-hint {
    @apply text-sm text-gray-500 dark:text-gray-400 italic;
}

.empty-hint code {
    @apply font-mono not-italic px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-xs;
}

.error-card {
    @apply mb-6;
}

.error-content {
    @apply flex items-center gap-2 text-error-600 dark:text-error-400;
}

.error-icon {
    @apply w-5 h-5;
}
</style>
