<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin'],
});

type Status = 'success' | 'warning' | 'error';

const api = useApi();
const { copy } = useClipboard({ legacy: true });
const { showSuccess } = useToastHelpers();

const checkedAt = ref('');
const { data, pending, refresh } = await useAsyncData<DatabaseHealthResponse>(
    'admin-db-health',
    async () => {
        const res = await api.get<DatabaseHealthResponse>('/admin/db-health');
        checkedAt.value = new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
        return res;
    },
    { server: false },
);

const view = ref<'tables' | 'indexes'>('tables');
const infoOpen = ref(false);
const showAllInfo = ref(false);
const INFO_PREVIEW = 5;

function getHealthColor(ratio: number, thresholdWarning: number, thresholdCritical: number): Status {
    if (ratio >= thresholdWarning) return 'success';
    if (ratio >= thresholdCritical) return 'warning';
    return 'error';
}

const TEXT: Record<Status, string> = { success: 'text-success', warning: 'text-warning', error: 'text-error' };
const BG: Record<Status, string> = { success: 'bg-success', warning: 'bg-warning', error: 'bg-error' };

const stats = computed(() => {
    const d = data.value;
    if (!d) return [];
    const connPct = d.max_connections ? (d.active_connections / d.max_connections) * 100 : 0;
    const connStatus = getHealthColor(100 - connPct, 20, 10);
    const cacheStatus = getHealthColor(d.cache_hit_ratio, 95, 90);
    const [size, unit] = d.database_size_pretty.split(' ');
    return [
        { label: 'Database size', value: size, unit, note: 'OK', noteClass: TEXT.success },
        {
            label: 'Connections',
            value: d.active_connections,
            unit: `/ ${d.max_connections}`,
            note: `${connPct.toFixed(0)}% used`,
            noteClass: TEXT[connStatus],
            meter: { pct: connPct, class: BG[connStatus] },
        },
        {
            label: 'Cache hit ratio',
            value: d.cache_hit_ratio.toFixed(1),
            unit: '%',
            note: cacheStatus === 'success' ? 'Healthy' : 'Needs attention',
            noteClass: TEXT[cacheStatus],
            meter: { pct: d.cache_hit_ratio, class: BG[cacheStatus] },
        },
        {
            label: 'Tables',
            value: d.tables.length,
            unit: '',
            note: `${d.indexes.length} indexes`,
            noteClass: 'text-muted',
        },
    ];
});

const issues = computed(() => (data.value?.recommendations ?? []).filter((r) => r.severity !== 'info'));
const infos = computed(() =>
    (data.value?.recommendations ?? []).filter((r) => r.severity === 'info' && r.type !== 'all_good'),
);
const infoSummary = computed(() => {
    const n = infos.value.length;
    if (infos.value.every((r) => r.type === 'unused_index'))
        return `${n} unused ${n === 1 ? 'index' : 'indexes'} could be dropped to save space`;
    return `${n} ${n === 1 ? 'suggestion' : 'suggestions'}`;
});

const headerPill = computed(() => {
    const n = issues.value.length;
    if (!n) return { label: 'Healthy', color: 'success' as const };
    const critical = issues.value.some((r) => r.severity === 'critical');
    return {
        label: `${n} ${n === 1 ? 'issue' : 'issues'}`,
        color: critical ? ('error' as const) : ('warning' as const),
    };
});

async function copyVacuumSql(table: string) {
    const sql = `VACUUM ANALYZE "${table}";`;
    await copy(sql);
    showSuccess('Copied', sql);
}

const maxSize = computed(() =>
    Math.max(
        1,
        ...(view.value === 'tables' ? (data.value?.tables ?? []) : (data.value?.indexes ?? [])).map((r) => r.size),
    ),
);

function formatVacuum(dateStr: string | null): string {
    return dateStr ? new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'Never';
}

const TABLE_GRID =
    'grid grid-cols-[minmax(0,1.2fr)_minmax(0,1.2fr)_56px] items-center gap-3 md:grid-cols-[minmax(0,1.6fr)_minmax(0,1.6fr)_70px_90px_80px_80px_90px]';
const INDEX_GRID =
    'grid grid-cols-[minmax(0,1.2fr)_minmax(0,1.2fr)_56px] items-center gap-3 md:grid-cols-[minmax(0,1.8fr)_minmax(0,1.4fr)_minmax(0,1fr)_70px_80px]';
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader
            title="Database health"
            :description="checkedAt ? `PostgreSQL · checked at ${checkedAt}` : 'PostgreSQL'"
        >
            <template v-if="data" #badges>
                <UBadge :label="headerPill.label" :color="headerPill.color" variant="soft" class="rounded-full">
                    <template #leading><span class="size-1.75 rounded-full bg-current" /></template>
                </UBadge>
            </template>
            <template #actions>
                <UButton
                    icon="i-lucide-refresh-cw"
                    label="Refresh"
                    color="neutral"
                    variant="outline"
                    size="lg"
                    :loading="pending"
                    @click="() => refresh()"
                />
            </template>
        </AdminPageHeader>

        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <div
                v-for="s in stats"
                :key="s.label"
                class="flex flex-col gap-2 rounded-xl border border-default bg-default px-4 py-3.5"
            >
                <span class="text-[13px] font-semibold text-muted">{{ s.label }}</span>
                <div class="flex items-baseline gap-1.5">
                    <span class="text-2xl font-extrabold text-highlighted tabular-nums">{{ s.value }}</span>
                    <span class="text-[13px] text-dimmed">{{ s.unit }}</span>
                </div>
                <span v-if="s.meter" class="flex h-1.5 overflow-hidden rounded-full bg-elevated">
                    <span
                        class="rounded-full"
                        :class="s.meter.class"
                        :style="{ width: `${Math.min(s.meter.pct, 100)}%` }"
                    />
                </span>
                <span class="text-xs font-bold" :class="s.noteClass">{{ s.note }}</span>
            </div>
        </div>

        <AdminCard v-if="issues.length || infos.length" :title="issues.length ? 'Needs attention' : 'Suggestions'">
            <div v-for="(rec, i) in issues" :key="i" class="flex flex-wrap items-center gap-3 px-4.5 py-3.5">
                <span
                    class="flex size-8 shrink-0 items-center justify-center rounded-lg"
                    :class="rec.severity === 'critical' ? 'bg-error/10 text-error' : 'bg-warning/10 text-warning'"
                >
                    <UIcon
                        :name="rec.severity === 'critical' ? 'i-lucide-octagon-alert' : 'i-lucide-triangle-alert'"
                        class="size-4"
                    />
                </span>
                <div class="flex min-w-50 flex-1 flex-col gap-0.5">
                    <span class="text-sm font-bold text-highlighted">{{ rec.action }}</span>
                    <span class="text-[13px] text-muted">{{ rec.message }}</span>
                </div>
                <UButton
                    v-if="rec.type === 'vacuum_needed' && rec.table"
                    icon="i-lucide-copy"
                    label="Copy SQL"
                    color="neutral"
                    variant="outline"
                    @click="copyVacuumSql(rec.table)"
                />
            </div>
            <div v-if="infos.length">
                <button
                    type="button"
                    class="flex w-full items-center gap-3 px-4.5 py-3 text-left hover:bg-elevated"
                    :aria-expanded="infoOpen"
                    @click="infoOpen = !infoOpen"
                >
                    <span class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-info/10 text-info">
                        <UIcon name="i-lucide-info" class="size-4" />
                    </span>
                    <span class="flex-1 text-sm font-bold text-highlighted">{{ infoSummary }}</span>
                    <UIcon :name="infoOpen ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'" class="text-muted" />
                </button>
                <div v-if="infoOpen" class="flex flex-col gap-1.5 pr-4.5 pb-3 pl-15.5">
                    <span
                        v-for="(rec, i) in showAllInfo ? infos : infos.slice(0, INFO_PREVIEW)"
                        :key="i"
                        class="font-mono text-[13px] [overflow-wrap:anywhere] text-muted"
                    >
                        {{ rec.message }}
                    </span>
                    <button
                        v-if="infos.length > INFO_PREVIEW"
                        type="button"
                        class="w-fit text-[13px] font-bold text-primary hover:underline"
                        @click="showAllInfo = !showAllInfo"
                    >
                        {{ showAllInfo ? 'Show less' : `Show all ${infos.length}` }}
                    </button>
                </div>
            </div>
        </AdminCard>

        <div class="flex flex-col gap-2.5">
            <AdminToolbar
                v-model:segment="view"
                :segments="[
                    { value: 'tables', label: 'Tables', count: data?.tables.length },
                    { value: 'indexes', label: 'Indexes', count: data?.indexes.length },
                ]"
            />

            <AdminCard v-if="view === 'tables'">
                <template #columns>
                    <div :class="TABLE_GRID">
                        <span>Table</span>
                        <span>Size</span>
                        <span>Rows</span>
                        <span class="hidden md:block">Dead tuples</span>
                        <span class="hidden md:block">Seq scans</span>
                        <span class="hidden md:block">Idx scans</span>
                        <span class="hidden md:block">Last vacuum</span>
                    </div>
                </template>
                <div v-for="t in data?.tables ?? []" :key="t.name" :class="TABLE_GRID" class="px-4.5 py-2.5 text-sm">
                    <span class="truncate font-mono text-[13px] text-highlighted" :title="t.name">{{ t.name }}</span>
                    <div class="flex min-w-0 items-center gap-2">
                        <span class="w-16 shrink-0 text-muted tabular-nums">{{ t.size_pretty }}</span>
                        <span class="flex h-1.5 flex-1 overflow-hidden rounded-full bg-elevated">
                            <span class="bg-primary opacity-70" :style="{ width: `${(t.size / maxSize) * 100}%` }" />
                        </span>
                    </div>
                    <span class="text-muted tabular-nums">{{ t.row_count.toLocaleString() }}</span>
                    <span
                        class="hidden tabular-nums md:block"
                        :class="t.dead_tuples > t.row_count * 0.1 ? 'font-bold text-warning' : 'text-muted'"
                    >
                        {{ t.dead_tuples.toLocaleString() }}
                    </span>
                    <span class="hidden text-muted tabular-nums md:block">{{ t.seq_scans.toLocaleString() }}</span>
                    <span class="hidden text-muted tabular-nums md:block">{{ t.idx_scans.toLocaleString() }}</span>
                    <span
                        class="hidden text-muted md:block"
                        :title="t.last_vacuum ? new Date(t.last_vacuum).toLocaleString() : undefined"
                    >
                        {{ formatVacuum(t.last_vacuum) }}
                    </span>
                </div>
            </AdminCard>

            <AdminCard v-else>
                <template #columns>
                    <div :class="INDEX_GRID">
                        <span>Index</span>
                        <span>Size</span>
                        <span class="hidden md:block">Table</span>
                        <span>Scans</span>
                        <span class="hidden md:block">Status</span>
                    </div>
                </template>
                <div v-for="ix in data?.indexes ?? []" :key="ix.name" :class="INDEX_GRID" class="px-4.5 py-2.5 text-sm">
                    <span class="truncate font-mono text-[13px] text-highlighted" :title="ix.name">{{ ix.name }}</span>
                    <div class="flex min-w-0 items-center gap-2">
                        <span class="w-16 shrink-0 text-muted tabular-nums">{{ ix.size_pretty }}</span>
                        <span class="flex h-1.5 flex-1 overflow-hidden rounded-full bg-elevated">
                            <span class="bg-primary opacity-70" :style="{ width: `${(ix.size / maxSize) * 100}%` }" />
                        </span>
                    </div>
                    <span class="hidden truncate font-mono text-[13px] text-muted md:block">{{ ix.table }}</span>
                    <span class="text-muted tabular-nums">{{ ix.scans.toLocaleString() }}</span>
                    <span class="hidden md:block">
                        <UBadge
                            :label="ix.is_unused ? 'Unused' : 'Active'"
                            :color="ix.is_unused ? 'warning' : 'success'"
                            variant="soft"
                            class="rounded-full"
                        />
                    </span>
                </div>
            </AdminCard>
        </div>
    </div>
</template>
