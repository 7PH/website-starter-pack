<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import { formatAction, formatDateTime, initials } from '~/utils/formatters';

definePageMeta({
    middleware: ['admin'],
});

const route = useRoute();
const router = useRouter();
const api = useApi();
const auth = useAuth();
const { showSuccess, showError } = useToastHelpers();
const modal = useModalStore();
const userDisplay = useUserDisplay();
const { impersonate } = useAdminImpersonation();
const backendConfig = useBackendConfig();

const userId = computed(() => Number(route.params.id));
const cmsEnabled = isCmsEnabled();

const {
    data: user,
    pending: userPending,
    refresh: refreshUser,
} = await useAsyncData<AdminUserRead>(`admin-user-${userId.value}`, () => api.get(`/admin/users/${userId.value}`), {
    server: false,
});

const { data: eventsData, pending: eventsPending } = await useAsyncData<EventLogListResponse>(
    `admin-user-events-${userId.value}`,
    () => api.get(`/admin/users/${userId.value}/events`),
    { server: false },
);

// CMS editors, fetched only in CMS mode
const { data: cmsEditors, refresh: refreshCmsEditors } = await useAsyncData<CmsEditorRead[]>(
    'admin-cms-editors',
    () => api.get('/cms/editors'),
    { server: false, immediate: cmsEnabled },
);
const isCmsEditor = computed(() => !!cmsEditors.value?.some((e) => e.user_id === userId.value));

const label = computed(() => (user.value ? userDisplay.label(user.value) : ''));

const activeTab = ref('overview');
const tabItems = computed(() => [
    { value: 'overview', label: 'Overview' },
    { value: 'organizations', label: 'Organizations', badge: user.value?.organizations?.length || undefined },
    { value: 'activity', label: 'Activity' },
]);

const SIGN_IN_METHODS: Record<string, string> = {
    password: 'Password',
    oauth: 'OAuth',
    access_code: 'Access code',
    deleted: 'Deleted',
};

// Two groups: the app's custom data block goes between them, so the card never ends on a hidden element.
const accountFields = computed(() => {
    const u = user.value;
    if (!u) return [];
    return [
        [
            { label: 'Name', value: [u.first_name, u.last_name].filter(Boolean).join(' ') },
            { label: 'Display name', value: u.display_name },
            ...(backendConfig.config?.usernames_enabled ? [{ label: 'Username', value: u.username }] : []),
            { label: 'Email', value: u.email },
        ],
        [
            { label: 'Sign-in method', value: SIGN_IN_METHODS[u.auth_method ?? 'password'] ?? u.auth_method },
            { label: 'Created', value: formatDateTime(u.created_at) },
            ...(u.deleted_at ? [{ label: 'Deleted', value: formatDateTime(u.deleted_at), error: true }] : []),
        ],
    ];
});

// Account edit form (admin rights are a toggle in the Permissions card)
const form = ref({
    first_name: '',
    last_name: '',
    display_name: '',
    username: '',
    email: '',
    is_premium: false,
    custom_data: {} as UserCustomData,
});
const isEditing = ref(false);
const isSaving = ref(false);

function formFromUser(u: AdminUserRead) {
    return {
        first_name: u.first_name ?? '',
        last_name: u.last_name ?? '',
        display_name: u.display_name ?? '',
        username: u.username ?? '',
        email: u.email ?? '',
        is_premium: u.is_premium ?? false,
        custom_data: (u.custom_data ?? {}) as UserCustomData,
    };
}

watch(
    user,
    (newUser) => {
        if (newUser) form.value = formFromUser(newUser);
    },
    { immediate: true },
);

async function saveChanges() {
    isSaving.value = true;
    try {
        await api.put(`/admin/users/${userId.value}`, form.value);
        showSuccess('User updated', 'Changes saved successfully');
        isEditing.value = false;
        refreshUser();
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        isSaving.value = false;
    }
}

function cancelEdit() {
    if (user.value) form.value = formFromUser(user.value);
    isEditing.value = false;
}

const savingAdmin = ref(false);

async function setAdmin(value: boolean) {
    savingAdmin.value = true;
    try {
        await api.put(`/admin/users/${userId.value}`, { is_admin: value });
        await refreshUser();
        showSuccess(value ? 'Now an administrator' : 'No longer an administrator');
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        savingAdmin.value = false;
    }
}

const savingCmsEditor = ref(false);

async function setCmsEditor(value: boolean) {
    savingCmsEditor.value = true;
    try {
        const path = `/cms/editors/${userId.value}`;
        await (value ? api.put(path, null) : api.delete(path));
        await refreshCmsEditors();
        showSuccess(value ? 'Can now edit the site' : 'Can no longer edit the site');
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        savingCmsEditor.value = false;
    }
}

async function deleteUser() {
    const confirmed = await modal.open('confirm', {
        title: 'Delete User',
        message: `Are you sure you want to delete ${label.value}? This action cannot be undone.`,
        confirmText: 'Delete',
        confirmColor: 'error',
    });
    if (!confirmed) return;

    try {
        await api.delete(`/admin/users/${userId.value}`);
        showSuccess('User deleted');
        await router.push('/admin/users');
    } catch (error) {
        showError(error, 'core.errors.generic');
    }
}

const ROW = 'grid gap-x-4 gap-y-1 px-4.5 py-3 text-sm md:grid-cols-[150px_minmax(0,1fr)]';
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <NuxtLink
            to="/admin/users"
            class="flex items-center gap-1.5 self-start text-[13px] font-bold text-muted hover:text-highlighted"
        >
            <UIcon name="i-lucide-arrow-left" />
            All users
        </NuxtLink>

        <div v-if="userPending" class="flex justify-center py-12">
            <UIcon name="i-lucide-loader-2" class="size-8 animate-spin text-primary" />
        </div>

        <UAlert v-else-if="!user" color="error" variant="subtle" icon="i-lucide-user-x" title="User not found" />

        <template v-else>
            <div class="flex flex-wrap items-center gap-4">
                <span
                    class="flex size-13 shrink-0 items-center justify-center rounded-full bg-primary-100 text-lg font-extrabold text-primary-700 md:size-15 dark:bg-primary-500/20 dark:text-primary-300"
                >
                    {{ initials(label) || '?' }}
                </span>
                <div class="flex min-w-45 flex-1 flex-col gap-1">
                    <h1 class="text-[22px] font-extrabold tracking-[-0.01em] text-highlighted md:text-[26px]">
                        {{ label }}
                    </h1>
                    <div class="flex flex-wrap items-center gap-2 text-sm text-muted">
                        <span>{{ user.email ?? 'No email' }}</span>
                        <span class="text-dimmed">·</span>
                        <span class="font-mono text-[13px]">#{{ user.id }}</span>
                    </div>
                    <div class="mt-1 flex flex-wrap gap-1.5">
                        <UBadge
                            v-if="user.deleted_at"
                            label="Deleted"
                            icon="i-lucide-trash-2"
                            color="error"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-if="user.is_admin"
                            label="Admin"
                            icon="i-lucide-shield"
                            color="info"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-if="user.is_premium"
                            label="Premium"
                            icon="i-lucide-star"
                            color="warning"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-if="user.auth_method === 'access_code'"
                            label="Access code"
                            icon="i-lucide-key-round"
                            color="neutral"
                            variant="soft"
                            class="rounded-full"
                        />
                        <UBadge
                            v-if="user.email && !user.email_confirmed && !user.deleted_at"
                            label="Email unverified"
                            icon="i-lucide-mail-warning"
                            color="warning"
                            variant="soft"
                            class="rounded-full"
                        />
                    </div>
                </div>
                <UButton
                    v-if="!user.deleted_at"
                    label="Impersonate"
                    icon="i-lucide-user-round-cog"
                    size="lg"
                    color="neutral"
                    variant="outline"
                    @click="impersonate(user.id, label)"
                />
            </div>

            <UAlert
                v-if="user.deleted_at"
                color="error"
                variant="subtle"
                icon="i-lucide-trash-2"
                title="This user has been deleted"
                :description="`Deleted on ${formatDateTime(user.deleted_at)}. Personal data has been anonymized.`"
            />

            <UTabs v-model="activeTab" :items="tabItems" variant="link" :content="false" />

            <div
                v-if="activeTab === 'overview'"
                class="grid items-start gap-4 md:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]"
            >
                <div class="flex min-w-0 flex-col gap-4">
                    <AdminCard title="Account">
                        <template #meta>
                            <UButton
                                v-if="!isEditing && !user.deleted_at"
                                label="Edit"
                                icon="i-lucide-pencil"
                                size="sm"
                                color="neutral"
                                variant="outline"
                                @click="isEditing = true"
                            />
                        </template>

                        <form v-if="isEditing" class="flex flex-col gap-4 px-4.5 py-4" @submit.prevent="saveChanges">
                            <div class="grid gap-4 sm:grid-cols-2">
                                <UFormField label="First name">
                                    <UInput v-model="form.first_name" class="w-full" />
                                </UFormField>
                                <UFormField label="Last name">
                                    <UInput v-model="form.last_name" class="w-full" />
                                </UFormField>
                            </div>
                            <UFormField
                                label="Display name"
                                hint="Overrides first/last for the visible label. Required for users with no first/last (access-code, kiosk, ...)."
                            >
                                <UInput v-model="form.display_name" class="w-full" />
                            </UFormField>
                            <UFormField
                                v-if="backendConfig.config?.usernames_enabled"
                                label="Username"
                                hint="Public handle. 2-32 characters: letters, numbers, _ - [ ]. Must be unique."
                            >
                                <UInput v-model="form.username" class="w-full" />
                            </UFormField>
                            <UFormField label="Email">
                                <UInput v-model="form.email" type="email" class="w-full" />
                            </UFormField>
                            <UCheckbox v-model="form.is_premium" label="Premium" />
                            <UsersMetadataFields
                                :custom-data="form.custom_data"
                                @update:custom-data="form.custom_data = $event"
                            />
                            <div class="flex justify-end gap-2">
                                <UButton label="Cancel" color="neutral" variant="outline" @click="cancelEdit" />
                                <UButton type="submit" label="Save changes" :loading="isSaving" />
                            </div>
                        </form>

                        <template v-else>
                            <template v-for="(fields, index) in accountFields">
                                <div v-for="field in fields" :key="field.label" :class="ROW">
                                    <span class="text-muted">{{ field.label }}</span>
                                    <span
                                        class="[overflow-wrap:anywhere]"
                                        :class="
                                            'error' in field
                                                ? 'text-error'
                                                : field.value
                                                  ? 'text-highlighted'
                                                  : 'text-dimmed'
                                        "
                                    >
                                        {{ field.value || 'Not set' }}
                                    </span>
                                </div>
                                <!-- App-defined custom data; hidden while the app leaves it empty -->
                                <div
                                    v-if="index === 0"
                                    :key="index"
                                    class="flex flex-col gap-3 px-4.5 py-3 has-[>:only-child:empty]:hidden"
                                >
                                    <UsersMetadataDisplay :custom-data="(user.custom_data ?? {}) as UserCustomData" />
                                </div>
                            </template>
                        </template>
                    </AdminCard>

                    <AdminCard title="Permissions">
                        <div class="flex items-center gap-3.5 px-4.5 py-3">
                            <div class="flex flex-1 flex-col gap-0.5">
                                <span class="text-sm font-bold text-highlighted">Administrator</span>
                                <span class="text-[13px] text-muted">
                                    {{
                                        user.id === auth.user?.id
                                            ? "You can't remove your own admin rights."
                                            : 'Full access to this admin area.'
                                    }}
                                </span>
                            </div>
                            <USwitch
                                :model-value="user.is_admin"
                                :disabled="!!user.deleted_at || user.id === auth.user?.id"
                                :loading="savingAdmin"
                                aria-label="Administrator"
                                @update:model-value="setAdmin"
                            />
                        </div>
                        <div v-if="cmsEnabled" class="flex items-center gap-3.5 px-4.5 py-3">
                            <div class="flex flex-1 flex-col gap-0.5">
                                <span class="text-sm font-bold text-highlighted">CMS editor</span>
                                <span class="text-[13px] text-muted">
                                    {{ user.is_admin ? 'Always on for administrators.' : 'Can edit pages and photos.' }}
                                </span>
                            </div>
                            <USwitch
                                :model-value="user.is_admin || isCmsEditor"
                                :disabled="user.is_admin || !!user.deleted_at"
                                :loading="savingCmsEditor"
                                aria-label="CMS editor"
                                @update:model-value="setCmsEditor"
                            />
                        </div>
                    </AdminCard>
                </div>

                <div class="flex min-w-0 flex-col gap-4">
                    <AdminCard title="Organizations" :meta="String(user.organizations?.length ?? 0)">
                        <NuxtLink
                            v-for="org in user.organizations"
                            :key="org.organization_id"
                            :to="`/admin/organizations/${org.organization_id}`"
                            class="flex items-center gap-2.5 px-4.5 py-3 hover:bg-elevated"
                        >
                            <span
                                class="flex size-7 shrink-0 items-center justify-center rounded-md bg-elevated text-[11px] font-extrabold text-toned"
                            >
                                {{ initials(org.organization_name) }}
                            </span>
                            <span class="min-w-0 flex-1 truncate text-sm font-semibold text-highlighted">
                                {{ org.organization_name }}
                            </span>
                            <span class="text-xs font-bold" :class="org.is_admin ? 'text-info' : 'text-muted'">
                                {{ org.is_admin ? 'Admin' : 'Member' }}
                            </span>
                        </NuxtLink>
                        <p v-if="!user.organizations?.length" class="px-4.5 py-3 text-sm text-muted">
                            Not a member of any organization.
                        </p>
                    </AdminCard>

                    <section
                        v-if="!user.deleted_at"
                        class="flex flex-col items-start gap-2.5 rounded-xl border border-error/30 px-4.5 py-3.5"
                    >
                        <h2 class="text-[15px] font-extrabold text-error">Danger zone</h2>
                        <p class="text-[13px] text-muted">
                            Deleting soft-deletes the account. It stays visible with “Show deleted”.
                        </p>
                        <UButton
                            label="Delete user"
                            icon="i-lucide-trash-2"
                            color="error"
                            variant="outline"
                            @click="deleteUser"
                        />
                    </section>
                </div>
            </div>

            <AdminCard v-else-if="activeTab === 'organizations'">
                <NuxtLink
                    v-for="org in user.organizations"
                    :key="org.organization_id"
                    :to="`/admin/organizations/${org.organization_id}`"
                    class="flex items-center gap-3 px-4.5 py-3 hover:bg-elevated"
                >
                    <span
                        class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-elevated text-xs font-extrabold text-toned"
                    >
                        {{ initials(org.organization_name) }}
                    </span>
                    <span class="min-w-0 flex-1 truncate text-sm font-bold text-primary">
                        {{ org.organization_name }}
                    </span>
                    <UBadge
                        v-if="org.has_premium_seat"
                        label="Premium seat"
                        color="warning"
                        variant="soft"
                        class="rounded-full"
                    />
                    <UBadge
                        :label="org.is_admin ? 'Admin' : 'Member'"
                        :color="org.is_admin ? 'info' : 'neutral'"
                        variant="soft"
                        class="rounded-full"
                    />
                </NuxtLink>
                <p v-if="!user.organizations?.length" class="px-4.5 py-8 text-center text-sm text-muted">
                    Not a member of any organization.
                </p>
            </AdminCard>

            <AdminCard v-else :class="{ 'opacity-60': eventsPending }">
                <div
                    v-for="event in eventsData?.items ?? []"
                    :key="event.id"
                    class="flex flex-wrap items-center gap-x-3 gap-y-1 px-4.5 py-3"
                >
                    <span class="size-2 shrink-0 rounded-full bg-primary" />
                    <span class="text-sm font-bold text-highlighted">{{ formatAction(event.action) }}</span>
                    <code
                        v-if="event.details && Object.keys(event.details).length"
                        class="max-w-full truncate rounded-[5px] bg-elevated px-1.5 py-px font-mono text-xs text-muted md:max-w-80"
                        :title="JSON.stringify(event.details)"
                    >
                        {{ JSON.stringify(event.details) }}
                    </code>
                    <span class="flex-1" />
                    <span v-if="event.ip_address" class="font-mono text-xs text-dimmed">{{ event.ip_address }}</span>
                    <span class="text-[13px] text-muted">{{ formatDateTime(event.created_at) }}</span>
                </div>
                <p v-if="!eventsData?.items.length" class="px-4.5 py-8 text-center text-sm text-muted">
                    {{ eventsPending ? 'Loading…' : 'No activity yet.' }}
                </p>
            </AdminCard>
        </template>
    </div>
</template>
