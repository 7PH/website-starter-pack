<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatDate, initials } from '~/utils/formatters';

definePageMeta({
    middleware: ['admin'],
});

const api = useApi();
const { impersonate } = useAdminImpersonation();

const { search, debouncedSearch, page, limit, offset } = useTableState({ defaultLimit: 100 });

const segment = ref('all');
const showDeleted = ref(false);
const SEGMENTS = [
    { value: 'all', label: 'All' },
    { value: 'admin', label: 'Admins' },
    ...(isCmsEnabled() ? [{ value: 'editor', label: 'Editors' }] : []),
    { value: 'premium', label: 'Premium' },
    { value: 'code', label: 'Access code' },
];

// useTableState resets page on debouncedSearch; reset on other filters too.
watch([segment, showDeleted], () => {
    page.value = 1;
});

const { data: usersData, pending } = await useAsyncData<AdminUserListResponse>(
    'admin-users',
    () =>
        api.get('/admin/users', {
            search: debouncedSearch.value || undefined,
            is_admin: segment.value === 'admin' || undefined,
            is_premium: segment.value === 'premium' || undefined,
            auth_method: segment.value === 'code' ? 'access_code' : undefined,
            cms_editor: segment.value === 'editor' || undefined,
            include_deleted: showDeleted.value || undefined,
            limit: limit.value,
            offset: offset.value,
        }),
    { watch: [debouncedSearch, segment, showDeleted, page], server: false },
);

// One extra request for the whole list, only in CMS mode.
const { data: cmsEditors } = await useAsyncData<CmsEditorRead[]>('admin-cms-editors', () => api.get('/cms/editors'), {
    server: false,
    immediate: isCmsEnabled(),
});
const cmsEditorIds = computed(() => new Set(cmsEditors.value?.map((e) => e.user_id)));

function nameLabel(user: AdminUserRead): string {
    return user.display_label ?? `User #${user.id}`;
}

const GRID = 'grid grid-cols-[minmax(0,1fr)_auto] md:grid-cols-[minmax(0,2.4fr)_60px_minmax(0,1.2fr)_90px_64px]';
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader
            title="Users"
            :count="usersData?.total"
            description="Click a user to see details, organizations and activity."
        />

        <AdminToolbar
            v-model:search="search"
            v-model:segment="segment"
            :segments="SEGMENTS"
            search-placeholder="Search by id, email or name"
        >
            <UCheckbox v-model="showDeleted" label="Show deleted" />
        </AdminToolbar>

        <AdminCard :class="{ 'opacity-60': pending }">
            <template #columns>
                <div :class="GRID" class="gap-3">
                    <span>User</span>
                    <span class="hidden md:block">ID</span>
                    <span>Status</span>
                    <span class="hidden md:block">Created</span>
                </div>
            </template>

            <div
                v-for="user in usersData?.items ?? []"
                :key="user.id"
                :class="GRID"
                class="relative items-center gap-3 px-4.5 py-3 hover:bg-elevated"
            >
                <div class="flex min-w-0 items-center gap-3">
                    <span
                        class="flex size-8.5 shrink-0 items-center justify-center rounded-full bg-elevated text-xs font-extrabold text-toned"
                    >
                        {{ initials(nameLabel(user)) || '?' }}
                    </span>
                    <div class="flex min-w-0 flex-col">
                        <!-- Stretched link: the whole row opens the user, the impersonate button stays clickable above it -->
                        <NuxtLink
                            :to="`/admin/users/${user.id}`"
                            class="truncate text-sm font-bold text-highlighted after:absolute after:inset-0"
                        >
                            {{ nameLabel(user) }}
                        </NuxtLink>
                        <span v-if="user.email" class="truncate text-[13px] text-muted">{{ user.email }}</span>
                        <span v-else-if="user.auth_method === 'access_code'" class="truncate text-[13px] text-dimmed">
                            No email · signs in with access code
                        </span>
                    </div>
                </div>
                <span class="hidden font-mono text-[13px] text-muted md:block">#{{ user.id }}</span>
                <div class="flex flex-wrap justify-end gap-1.5 md:justify-start">
                    <UBadge v-if="user.deleted_at" label="Deleted" color="error" variant="soft" class="rounded-full" />
                    <UBadge v-if="user.is_admin" label="Admin" color="info" variant="soft" class="rounded-full" />
                    <UBadge
                        v-if="user.is_premium"
                        label="Premium"
                        color="warning"
                        variant="soft"
                        class="rounded-full"
                    />
                    <UBadge
                        v-if="cmsEditorIds.has(user.id)"
                        label="Editor"
                        color="primary"
                        variant="soft"
                        class="rounded-full"
                    />
                    <UBadge
                        v-if="user.auth_method === 'access_code'"
                        label="Access code"
                        color="neutral"
                        variant="soft"
                        class="rounded-full"
                    />
                </div>
                <span class="hidden text-[13px] text-muted md:block">{{ formatDate(user.created_at) }}</span>
                <div class="hidden items-center justify-end gap-0.5 text-dimmed md:flex">
                    <UTooltip v-if="!user.deleted_at" text="Impersonate">
                        <UButton
                            icon="i-lucide-user-round-cog"
                            color="neutral"
                            variant="ghost"
                            aria-label="Impersonate"
                            class="relative"
                            @click="impersonate(user.id, nameLabel(user))"
                        />
                    </UTooltip>
                    <UIcon name="i-lucide-chevron-right" class="size-4" />
                </div>
            </div>

            <p v-if="!usersData?.items.length" class="px-4.5 py-8 text-center text-sm text-muted">
                {{ pending ? 'Loading…' : search ? `No user matches “${search}”` : 'No users found' }}
            </p>

            <AdminPagination v-model:page="page" :total="usersData?.total ?? 0" :limit="limit" />
        </AdminCard>
    </div>
</template>
