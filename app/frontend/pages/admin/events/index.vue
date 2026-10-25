<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatAction } from '~/utils/formatters';

definePageMeta({
    middleware: ['admin'],
});

const api = useApi();
const { showError } = useToastHelpers();
const PAGE_SIZE = 50;

// One chip = one action prefix, the only kind of action filter the API supports
const CHIPS = [
    { value: '', label: 'All', dot: 'bg-(--ui-text-dimmed)' },
    { value: 'user.login', label: 'Sign-ins', dot: 'bg-success' },
    { value: 'user.', label: 'Users', dot: 'bg-(--ui-text-muted)' },
    { value: 'admin.', label: 'Admin changes', dot: 'bg-info' },
    { value: 'org.', label: 'Organizations', dot: 'bg-primary' },
    { value: 'conversation.', label: 'Support', dot: 'bg-warning' },
];

const LABELS: Record<string, string> = {
    'user.login': 'Signed in',
    'user.login_code': 'Signed in with access code',
    'user.login_code_fail': 'Access code sign-in failed',
    'user.logout': 'Signed out',
    'user.register': 'Registered',
    'user.profile_update': 'Updated profile',
    'user.password_change': 'Changed password',
    'user.password_reset_request': 'Requested password reset',
    'user.password_reset': 'Reset password',
    'user.email_verify': 'Verified email',
    'admin.user_update': 'Admin updated user',
    'admin.user_delete': 'Admin deleted user',
    'admin.impersonate_start': 'Impersonation started',
    'admin.impersonate_stop': 'Impersonation stopped',
};

const actionPrefix = ref('');
const userIdFilter = ref('');
const fromDateStr = ref('');
const toDateStr = ref('');

const events = ref<EventLogRead[]>([]);
const total = ref(0);
const loading = ref(false);
let lastRequest = 0;

async function load(append = false) {
    const request = ++lastRequest;
    loading.value = true;
    try {
        const res = await api.get<EventLogListResponse>('/admin/events', {
            action_prefix: actionPrefix.value || undefined,
            user_id: userIdFilter.value ? Number(userIdFilter.value) : undefined,
            from_date: fromDateStr.value ? new Date(fromDateStr.value).toISOString() : undefined,
            to_date: toDateStr.value ? new Date(toDateStr.value).toISOString() : undefined,
            limit: PAGE_SIZE,
            offset: append ? events.value.length : 0,
        });
        // A newer request (eg a filter clicked meanwhile) owns the list now
        if (request !== lastRequest) return;
        events.value = append ? [...events.value, ...res.items] : res.items;
        total.value = res.total;
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        if (request === lastRequest) loading.value = false;
    }
}

watch([actionPrefix, userIdFilter, fromDateStr, toDateStr], () => load(), { immediate: true });

const hasFilters = computed(() => !!(actionPrefix.value || userIdFilter.value || fromDateStr.value || toDateStr.value));

function clearFilters() {
    actionPrefix.value = '';
    userIdFilter.value = '';
    fromDateStr.value = '';
    toDateStr.value = '';
}

const shortDate = (s: string) => new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
const dateLabel = computed(() => {
    if (fromDateStr.value && toDateStr.value) return `${shortDate(fromDateStr.value)} – ${shortDate(toDateStr.value)}`;
    if (fromDateStr.value) return `Since ${shortDate(fromDateStr.value)}`;
    if (toDateStr.value) return `Until ${shortDate(toDateStr.value)}`;
    return 'Any time';
});

function eventLabel(action: string): string {
    return LABELS[action] ?? formatAction(action.replaceAll('_', ' '));
}

function eventDot(action: string): string {
    if (action.includes('delete') || action.endsWith('_fail')) return 'bg-error';
    if (action.startsWith('user.login') || action === 'user.register') return 'bg-success';
    if (action.startsWith('admin.')) return 'bg-info';
    if (action.startsWith('org.')) return 'bg-primary';
    if (action.startsWith('conversation.')) return 'bg-warning';
    return 'bg-(--ui-text-dimmed)';
}

function show(value: unknown): string {
    if (value === null || value === undefined || value === '') return '∅';
    const text = typeof value === 'object' ? JSON.stringify(value) : String(value);
    return text.length > 60 ? `${text.slice(0, 59)}…` : text;
}

type DetailChip = { key: string; from?: string; to: string };

// details.changes ({key: {from, to}}) become diff chips; other detail keys become plain key/value chips
function detailChips(details: EventLogRead['details']): DetailChip[] {
    const { changes, ...rest } = (details ?? {}) as Record<string, unknown>;
    const diffs = Object.entries((changes ?? {}) as Record<string, { from?: unknown; to?: unknown }>).map(
        ([key, c]) => ({ key, from: show(c?.from), to: show(c?.to) }),
    );
    const values = Object.entries(rest).map(([key, value]) => ({ key, to: show(value) }));
    return [...diffs, ...values];
}

const days = computed(() => {
    const groups: { date: string; items: (EventLogRead & { time: string; chips: DetailChip[] })[] }[] = [];
    for (const e of events.value) {
        const d = new Date(e.created_at!);
        const date = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        const item = {
            ...e,
            time: d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
            chips: detailChips(e.details),
        };
        const last = groups.at(-1);
        if (last?.date === date) last.items.push(item);
        else groups.push({ date, items: [item] });
    }
    return groups;
});

const chipClass = (active: boolean) =>
    active
        ? 'border-transparent bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-300'
        : 'border-default bg-default text-muted hover:text-highlighted';
const dashedChipClass = (active: boolean) =>
    active
        ? 'border-transparent bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-300'
        : 'border-dashed border-default text-muted hover:text-highlighted';
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader title="Events" :count="total" description="Audit log of sign-ins and account changes.">
            <template #actions>
                <UTooltip text="Refresh">
                    <UButton
                        icon="i-lucide-refresh-cw"
                        color="neutral"
                        variant="outline"
                        size="lg"
                        aria-label="Refresh"
                        :loading="loading"
                        @click="load()"
                    />
                </UTooltip>
            </template>
        </AdminPageHeader>

        <div class="flex flex-wrap items-center gap-2">
            <button
                v-for="c in CHIPS"
                :key="c.value"
                type="button"
                :aria-pressed="c.value === actionPrefix"
                class="flex h-8.5 items-center gap-1.5 rounded-full border px-3 text-[13px] font-bold transition-colors"
                :class="chipClass(c.value === actionPrefix)"
                @click="actionPrefix = c.value"
            >
                <span class="size-1.75 rounded-full" :class="c.dot" />
                {{ c.label }}
            </button>
            <span class="mx-1 h-5.5 w-px bg-(--ui-border)" />
            <UPopover>
                <button
                    type="button"
                    class="flex h-8.5 items-center gap-1.5 rounded-full border px-3 text-[13px] font-bold transition-colors"
                    :class="dashedChipClass(!!userIdFilter)"
                >
                    <UIcon name="i-lucide-user" />
                    {{ userIdFilter ? `User #${userIdFilter}` : 'User' }}
                </button>
                <template #content>
                    <div class="flex flex-col gap-2 p-3">
                        <span class="text-xs font-bold text-muted">User ID</span>
                        <UInput
                            v-model.lazy="userIdFilter"
                            type="number"
                            placeholder="e.g. 15"
                            class="w-40"
                            autofocus
                        />
                    </div>
                </template>
            </UPopover>
            <UPopover>
                <button
                    type="button"
                    class="flex h-8.5 items-center gap-1.5 rounded-full border px-3 text-[13px] font-bold transition-colors"
                    :class="dashedChipClass(!!(fromDateStr || toDateStr))"
                >
                    <UIcon name="i-lucide-calendar" />
                    {{ dateLabel }}
                </button>
                <template #content>
                    <div class="flex flex-col gap-2 p-3">
                        <span class="text-xs font-bold text-muted">From</span>
                        <UInput v-model="fromDateStr" type="datetime-local" class="w-56" />
                        <span class="text-xs font-bold text-muted">To</span>
                        <UInput v-model="toDateStr" type="datetime-local" class="w-56" />
                    </div>
                </template>
            </UPopover>
            <UButton
                v-if="hasFilters"
                label="Clear"
                icon="i-lucide-x"
                color="neutral"
                variant="ghost"
                size="sm"
                @click="clearFilters"
            />
        </div>

        <div class="flex flex-col gap-5">
            <div v-for="day in days" :key="day.date" class="flex flex-col gap-2">
                <span class="text-xs font-extrabold tracking-[.06em] text-dimmed uppercase">{{ day.date }}</span>
                <AdminCard>
                    <div
                        v-for="e in day.items"
                        :key="e.id"
                        class="grid grid-cols-[auto_minmax(0,1fr)] items-center gap-x-3.5 gap-y-1.5 px-4.5 py-2.75 md:grid-cols-[76px_minmax(0,1.3fr)_minmax(0,1.6fr)_120px]"
                    >
                        <span class="text-[13px] text-muted tabular-nums">{{ e.time }}</span>
                        <div class="flex min-w-0 items-center gap-2">
                            <span class="size-2 shrink-0 rounded-full" :class="eventDot(e.action)" />
                            <span class="truncate text-sm font-bold text-highlighted" :title="e.action">
                                {{ eventLabel(e.action) }}
                            </span>
                            <NuxtLink
                                v-if="e.user_id"
                                :to="`/admin/users/${e.user_id}`"
                                class="text-[13px] font-semibold text-primary hover:underline"
                            >
                                #{{ e.user_id }}
                            </NuxtLink>
                        </div>
                        <div
                            class="col-span-2 min-w-0 flex-wrap gap-1.5 md:col-span-1 md:flex"
                            :class="e.chips.length ? 'flex' : 'hidden'"
                        >
                            <span
                                v-for="chip in e.chips"
                                :key="chip.key"
                                class="flex min-w-0 items-center gap-1.5 rounded-md bg-elevated px-2 py-0.75 font-mono text-xs [overflow-wrap:anywhere]"
                            >
                                <span class="text-dimmed">{{ chip.key }}</span>
                                <template v-if="chip.from !== undefined">
                                    <span class="text-muted line-through">{{ chip.from }}</span>
                                    <span class="text-dimmed">→</span>
                                </template>
                                <span class="font-bold text-highlighted">{{ chip.to }}</span>
                            </span>
                        </div>
                        <span class="hidden truncate font-mono text-xs text-dimmed md:block">{{ e.ip_address }}</span>
                    </div>
                </AdminCard>
            </div>

            <AdminCard v-if="!loading && !events.length">
                <p class="px-4.5 py-8 text-center text-sm text-muted">No events match these filters.</p>
            </AdminCard>

            <UButton
                v-if="events.length < total"
                label="Load older events"
                color="neutral"
                variant="outline"
                class="self-center"
                :loading="loading"
                @click="load(true)"
            />
        </div>
    </div>
</template>
