<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatDate, initials } from '~/utils/formatters';
import { yesNoToBool } from '~/utils/admin-filters';

definePageMeta({
    middleware: ['admin'],
});

const api = useApi();
const { showSuccess, showError } = useToastHelpers();

const { search, debouncedSearch, page, limit, offset } = useTableState({ defaultLimit: 100 });

const planFilter = ref('all');
const showDeleted = ref(false);
const PLAN_OPTIONS = [
    { label: 'Any plan', value: 'all' },
    { label: 'Premium', value: 'yes' },
    { label: 'Free', value: 'no' },
];

// useTableState resets page on debouncedSearch; reset on other filters too.
watch([planFilter, showDeleted], () => {
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
            search: debouncedSearch.value || undefined,
            stripe_premium: yesNoToBool(planFilter.value),
            include_deleted: showDeleted.value || undefined,
            limit: limit.value,
            offset: offset.value,
        }),
    { watch: [debouncedSearch, planFilter, showDeleted, page], server: false },
);

function seats(org: OrganizationRead) {
    const used = org.premium_member_count ?? 0;
    return {
        used,
        over: used > org.stripe_quota,
        pct: org.stripe_quota ? Math.min(100, (used / org.stripe_quota) * 100) : 100,
    };
}

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

const GRID = 'grid grid-cols-[minmax(0,1fr)_auto] md:grid-cols-[minmax(0,2.2fr)_minmax(0,1.3fr)_100px_90px_24px]';
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader
            title="Organizations"
            :count="orgsData?.total"
            description="Teams that share a subscription and premium seats."
        >
            <template #actions>
                <UButton label="New organization" icon="i-lucide-plus" size="lg" @click="showCreateModal = true" />
            </template>
        </AdminPageHeader>

        <AdminToolbar v-model:search="search" search-placeholder="Search by name or email">
            <USelect v-model="planFilter" :items="PLAN_OPTIONS" size="lg" class="w-36" />
            <UCheckbox v-model="showDeleted" label="Show deleted" />
        </AdminToolbar>

        <AdminCard :class="{ 'opacity-60': pending }">
            <template #columns>
                <div :class="GRID" class="gap-3">
                    <span>Organization</span>
                    <span class="text-right md:text-left">Members</span>
                    <span class="hidden md:block">Plan</span>
                    <span class="hidden md:block">Created</span>
                </div>
            </template>

            <NuxtLink
                v-for="org in orgsData?.items ?? []"
                :key="org.id"
                :to="`/admin/organizations/${org.id}`"
                :class="GRID"
                class="items-center gap-x-3 gap-y-2 px-4.5 py-3 hover:bg-elevated"
            >
                <div class="flex min-w-0 items-center gap-3">
                    <span
                        class="flex size-8.5 shrink-0 items-center justify-center rounded-[9px] bg-elevated text-xs font-extrabold text-toned"
                    >
                        {{ initials(org.name) }}
                    </span>
                    <div class="flex min-w-0 flex-col">
                        <span class="truncate text-sm font-bold text-highlighted">{{ org.name }}</span>
                        <span class="truncate text-[13px] text-muted">{{ org.email }}</span>
                    </div>
                </div>
                <div class="flex flex-col items-end gap-1 md:items-start">
                    <span class="text-[13px] text-highlighted">
                        {{ org.member_count }} {{ org.member_count === 1 ? 'member' : 'members' }}
                    </span>
                    <div v-if="org.stripe_premium" class="flex items-center gap-1.5">
                        <span class="flex h-1.25 w-15 overflow-hidden rounded-full bg-elevated">
                            <span
                                :class="seats(org).over ? 'bg-error' : 'bg-warning'"
                                :style="{ width: `${seats(org).pct}%` }"
                            />
                        </span>
                        <span class="text-xs" :class="seats(org).over ? 'font-bold text-error' : 'text-muted'">
                            {{ seats(org).used }} / {{ org.stripe_quota }} premium seats
                        </span>
                    </div>
                </div>
                <span class="hidden gap-1 md:flex md:flex-wrap">
                    <UBadge v-if="org.deleted_at" label="Deleted" color="error" variant="soft" class="rounded-full" />
                    <UBadge
                        v-else
                        :label="org.stripe_premium ? 'Premium' : 'Free'"
                        :color="org.stripe_premium ? 'warning' : 'neutral'"
                        variant="soft"
                        class="rounded-full"
                    />
                </span>
                <span class="hidden text-[13px] text-muted md:block">{{ formatDate(org.created_at) }}</span>
                <UIcon name="i-lucide-chevron-right" class="hidden size-4 text-dimmed md:block" />
            </NuxtLink>

            <p v-if="!orgsData?.items.length" class="px-4.5 py-8 text-center text-sm text-muted">
                {{ pending ? 'Loading…' : search ? `No organization matches “${search}”` : 'No organizations found' }}
            </p>

            <AdminPagination v-model:page="page" :total="orgsData?.total ?? 0" :limit="limit" />
        </AdminCard>

        <OrganizationsCreateModal
            v-model:open="showCreateModal"
            :is-creating="isCreating"
            @create="createOrganization"
        />
    </div>
</template>
