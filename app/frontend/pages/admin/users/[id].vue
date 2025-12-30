<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    layout: 'admin',
    middleware: ['admin'],
});

const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const modal = useModalStore();

const userId = computed(() => Number(route.params.id));

// Fetch user data
const {
    data: user,
    pending: userPending,
    refresh: refreshUser,
} = await useAsyncData<AdminUserRead>(
    `admin-user-${userId.value}`,
    () => api.get(`/admin/users/${userId.value}`),
    { server: false },
);

// Fetch user events
const { data: eventsData, pending: eventsPending } = await useAsyncData<EventLogListResponse>(
    `admin-user-events-${userId.value}`,
    () => api.get(`/admin/users/${userId.value}/events`),
    { server: false },
);

// Form state
const form = ref({
    first_name: '',
    last_name: '',
    email: '',
    is_admin: false,
    is_premium: false,
});

const isEditing = ref(false);
const isSaving = ref(false);

// Event log table columns
const eventColumns = [
    { accessorKey: 'action', header: 'Action' },
    { accessorKey: 'created_at', header: 'Time' },
    { accessorKey: 'details', header: 'Details' },
];

// Initialize form when user data loads
watch(
    user,
    (newUser) => {
        if (newUser) {
            form.value = {
                first_name: newUser.first_name,
                last_name: newUser.last_name,
                email: newUser.email,
                is_admin: newUser.is_admin,
                is_premium: newUser.is_premium,
            };
        }
    },
    { immediate: true },
);

function formatDate(dateStr: string | null): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
}

function formatAction(action: string): string {
    return action
        .split('.')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
}

async function saveChanges() {
    isSaving.value = true;
    try {
        await api.put(`/admin/users/${userId.value}`, form.value);
        toast.add({
            title: 'User updated',
            description: 'Changes saved successfully',
            color: 'success',
            duration: 3000,
        });
        isEditing.value = false;
        refreshUser();
    } catch (error) {
        toast.add({
            title: 'Error',
            description: 'Failed to save changes',
            color: 'error',
            duration: 3000,
        });
    } finally {
        isSaving.value = false;
    }
}

function cancelEdit() {
    if (user.value) {
        form.value = {
            first_name: user.value.first_name,
            last_name: user.value.last_name,
            email: user.value.email,
            is_admin: user.value.is_admin,
            is_premium: user.value.is_premium,
        };
    }
    isEditing.value = false;
}

async function impersonateUser() {
    if (!user.value) return;

    try {
        const response = await api.post<ImpersonationResponse>(`/admin/impersonate/${userId.value}`);
        const auth = useAuth();

        auth.saveUserToken({
            access_token: response.access_token,
            token_parsed: response.token_parsed,
            user: response.user,
            token_type: 'bearer',
        });

        toast.add({
            title: 'Impersonation started',
            description: `Now viewing as ${user.value.email}`,
            color: 'success',
            duration: 3000,
        });

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

async function deleteUser() {
    if (!user.value) return;

    const confirmed = await modal.open('confirm', {
        title: 'Delete User',
        message: `Are you sure you want to delete ${user.value.email}? This action cannot be undone.`,
        confirmText: 'Delete',
        confirmColor: 'error',
    });

    if (!confirmed) return;

    try {
        await api.delete(`/admin/users/${userId.value}`);
        toast.add({
            title: 'User deleted',
            color: 'success',
            duration: 3000,
        });
        await router.push('/admin/users');
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
    <div class="user-detail">
        <!-- Back link -->
        <NuxtLink to="/admin/users" class="back-link">
            <UIcon name="i-lucide-arrow-left" />
            Back to Users
        </NuxtLink>

        <div v-if="userPending" class="loading">
            <UIcon name="i-lucide-loader-2" class="animate-spin text-4xl text-primary-500" />
        </div>

        <template v-else-if="user">
            <!-- Header -->
            <div class="page-header">
                <div class="header-info">
                    <h1 class="page-title">{{ user.first_name }} {{ user.last_name }}</h1>
                    <span class="user-email">{{ user.email }}</span>
                    <div class="badges">
                        <UBadge v-if="user.is_admin" label="Admin" color="info" />
                        <UBadge v-if="user.is_premium" label="Premium" color="warning" />
                        <UBadge v-if="user.email_confirmed" label="Verified" color="success" />
                        <UBadge v-else label="Unverified" color="neutral" />
                    </div>
                </div>
                <div class="header-actions">
                    <UButton label="Impersonate" icon="i-lucide-user" color="neutral" variant="outline" @click="impersonateUser" />
                    <UButton label="Delete" icon="i-lucide-trash-2" color="error" variant="outline" @click="deleteUser" />
                </div>
            </div>

            <div class="content-grid">
                <!-- User Info Card -->
                <UCard class="info-card">
                    <template #header>
                        <div class="card-header">
                            <span class="font-semibold">User Information</span>
                            <UButton
                                v-if="!isEditing"
                                label="Edit"
                                icon="i-lucide-pencil"
                                size="sm"
                                color="neutral"
                                variant="outline"
                                @click="isEditing = true"
                            />
                        </div>
                    </template>

                    <form v-if="isEditing" class="edit-form" @submit.prevent="saveChanges">
                        <div class="form-row">
                            <UFormField label="First Name" class="flex-1">
                                <UInput v-model="form.first_name" />
                            </UFormField>
                            <UFormField label="Last Name" class="flex-1">
                                <UInput v-model="form.last_name" />
                            </UFormField>
                        </div>
                        <UFormField label="Email">
                            <UInput v-model="form.email" type="email" />
                        </UFormField>
                        <div class="form-row">
                            <UCheckbox v-model="form.is_admin" label="Admin" />
                            <UCheckbox v-model="form.is_premium" label="Premium" />
                        </div>
                        <div class="form-actions">
                            <UButton label="Cancel" color="neutral" variant="outline" @click="cancelEdit" />
                            <UButton type="submit" label="Save Changes" :loading="isSaving" />
                        </div>
                    </form>

                    <div v-else class="info-grid">
                        <div class="info-item">
                            <span class="info-label">User ID</span>
                            <span class="info-value">#{{ user.id }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Email</span>
                            <span class="info-value">{{ user.email }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Name</span>
                            <span class="info-value">{{ user.first_name }} {{ user.last_name }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Created</span>
                            <span class="info-value">{{ formatDate(user.created_at) }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Last Seen</span>
                            <span class="info-value">{{ formatDate(user.last_seen_at) }}</span>
                        </div>
                    </div>
                </UCard>

                <!-- Event Log Card -->
                <UCard class="events-card">
                    <template #header>
                        <span class="font-semibold">Event Log</span>
                    </template>

                    <UTable
                        :columns="eventColumns"
                        :data="eventsData?.items ?? []"
                        :loading="eventsPending"
                        class="max-h-[400px] overflow-auto"
                    >
                        <template #action-cell="{ row }">
                            <UBadge :label="formatAction(row.original.action)" />
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
                </UCard>
            </div>
        </template>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.user-detail {
    @apply max-w-7xl mx-auto;
}

.back-link {
    @apply inline-flex items-center gap-2 text-gray-500 dark:text-gray-400 no-underline text-sm mb-4;
}

.back-link:hover {
    @apply text-primary-500;
}

.loading {
    @apply flex justify-center py-12;
}

.page-header {
    @apply flex justify-between items-start mb-6;
}

.header-info {
    @apply flex flex-col gap-2;
}

.page-title {
    @apply text-2xl font-semibold m-0 text-gray-900 dark:text-gray-100;
}

.user-email {
    @apply text-gray-500 dark:text-gray-400;
}

.badges {
    @apply flex gap-2;
}

.header-actions {
    @apply flex gap-2;
}

.content-grid {
    @apply grid grid-cols-1 lg:grid-cols-2 gap-6;
}

.card-header {
    @apply flex justify-between items-center;
}

.info-grid {
    @apply grid gap-4;
}

.info-item {
    @apply flex flex-col gap-1;
}

.info-label {
    @apply text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide;
}

.info-value {
    @apply text-sm text-gray-900 dark:text-gray-100;
}

.edit-form {
    @apply flex flex-col gap-4;
}

.form-row {
    @apply grid grid-cols-2 gap-4;
}

.form-field {
    @apply flex flex-col gap-2;
}

.form-field.checkbox {
    @apply flex-row items-center;
}

.form-field label {
    @apply text-sm font-medium text-gray-700 dark:text-gray-300;
}

.form-actions {
    @apply flex justify-end gap-2 mt-2;
}

.details-code {
    @apply text-xs bg-gray-100 dark:bg-gray-700 py-1 px-2 rounded max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap inline-block;
}

.text-muted {
    @apply text-gray-500 dark:text-gray-400;
}
</style>
