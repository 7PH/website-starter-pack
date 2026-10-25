<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin'],
});

const backendConfig = useBackendConfig();
const query = ref('');

// First matching prefix wins; keys matching none go to "Other".
const GROUPS: [prefix: string, label: string][] = [
    ['llm_', 'AI / LLM'],
    ['managed_', 'Managed accounts'],
    ['org', 'Organizations'],
    ['password_', 'Authentication'],
];

const groups = computed(() => {
    const cfg = (backendConfig.config ?? {}) as Record<string, unknown>;
    const q = query.value.trim().toLowerCase();
    const byLabel = new Map<string, { key: string; value: unknown }[]>();
    for (const key of Object.keys(cfg).sort()) {
        if (q && !key.toLowerCase().includes(q)) continue;
        const label = GROUPS.find(([prefix]) => key.startsWith(prefix))?.[1] ?? 'Other';
        byLabel.set(label, [...(byLabel.get(label) ?? []), { key, value: cfg[key] }]);
    }
    return [...GROUPS.map(([, label]) => label), 'Other']
        .filter((label) => byLabel.has(label))
        .map((label) => ({ label, rows: byLabel.get(label)! }));
});
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader title="Configuration">
            <template #badges>
                <UBadge icon="i-lucide-lock" label="Read-only" color="neutral" variant="soft" class="rounded-full" />
            </template>
            <template #description>
                Public config served by <code class="font-mono text-[13px]">/api/v1/config</code>, as the frontend sees
                it.
            </template>
            <template #actions>
                <UInput
                    v-model="query"
                    icon="i-lucide-search"
                    size="lg"
                    placeholder="Filter keys"
                    class="w-full sm:w-60"
                />
            </template>
        </AdminPageHeader>

        <UAlert
            v-if="!backendConfig.config"
            color="error"
            variant="subtle"
            icon="i-lucide-alert-triangle"
            title="Failed to load config from /api/v1/config."
        />

        <AdminCard
            v-for="group in groups"
            :key="group.label"
            :title="group.label"
            :meta="`${group.rows.length} ${group.rows.length === 1 ? 'key' : 'keys'}`"
        >
            <div
                v-for="row in group.rows"
                :key="row.key"
                class="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1 px-4.5 py-2.5 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_80px]"
            >
                <span class="font-mono text-[13px] [overflow-wrap:anywhere] text-highlighted">{{ row.key }}</span>
                <span v-if="typeof row.value === 'boolean'" class="flex items-center gap-1.5 text-[13px] font-bold">
                    <span class="size-2 rounded-full" :class="row.value ? 'bg-success' : 'bg-(--ui-text-dimmed)'" />
                    <span :class="row.value ? 'text-highlighted' : 'text-muted'">{{ row.value ? 'On' : 'Off' }}</span>
                </span>
                <span v-else-if="row.value === '' || row.value == null" class="text-[13px] text-dimmed italic">
                    {{ row.value === '' ? '(empty)' : 'Not set' }}
                </span>
                <span
                    v-else
                    class="w-fit rounded-[5px] bg-elevated px-1.5 py-px font-mono text-[13px] [overflow-wrap:anywhere] text-highlighted"
                >
                    {{ row.value }}
                </span>
                <span class="hidden text-right font-mono text-xs text-dimmed md:block">{{ typeof row.value }}</span>
            </div>
        </AdminCard>

        <AdminCard v-if="backendConfig.config && !groups.length">
            <p class="px-4.5 py-8 text-center text-sm text-muted">No key matches “{{ query }}”</p>
        </AdminCard>
    </div>
</template>
