<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin'],
});

const api = useApi();
const auth = useAuth();
const toast = useToast();

const creating = ref(false);
const deleting = ref<string | null>(null);
const showDeleteModal = ref(false);
const backupToDelete = ref<string | null>(null);

// Table columns
const columns = [
    { accessorKey: 'filename', header: 'Filename' },
    { accessorKey: 'size', header: 'Size' },
    { accessorKey: 'created_at', header: 'Created' },
    { accessorKey: 'actions', header: 'Actions' },
];

const {
    data: backupsData,
    pending,
    refresh,
} = await useAsyncData<BackupListResponse>('admin-backups', () => api.get('/admin/backups'), { server: false });

function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString();
}

function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

async function createBackup() {
    creating.value = true;
    try {
        await api.post('/admin/backups');
        toast.add({
            title: 'Backup created',
            description: 'Database backup completed successfully',
            color: 'success',
            duration: 3000,
        });
        refresh();
    } catch {
        toast.add({
            title: 'Backup failed',
            description: 'Failed to create database backup',
            color: 'error',
            duration: 5000,
        });
    } finally {
        creating.value = false;
    }
}

async function downloadBackup(filename: string) {
    const basepath = useRuntimeConfig().public.apiBase;
    const url = `${basepath}/admin/backups/${filename}`;

    try {
        const response = await fetch(url, {
            headers: {
                Authorization: `Bearer ${auth.token?.access_token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Download failed');
        }

        const blob = await response.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
        URL.revokeObjectURL(link.href);
    } catch {
        toast.add({
            title: 'Download failed',
            description: 'Failed to download backup file',
            color: 'error',
            duration: 3000,
        });
    }
}

function confirmDelete(filename: string) {
    backupToDelete.value = filename;
    showDeleteModal.value = true;
}

async function deleteBackup() {
    if (!backupToDelete.value) return;

    deleting.value = backupToDelete.value;
    try {
        await api.delete(`/admin/backups/${backupToDelete.value}`);
        toast.add({
            title: 'Backup deleted',
            description: 'Backup file removed successfully',
            color: 'success',
            duration: 3000,
        });
        refresh();
    } catch {
        toast.add({
            title: 'Delete failed',
            description: 'Failed to delete backup file',
            color: 'error',
            duration: 5000,
        });
    } finally {
        deleting.value = null;
        showDeleteModal.value = false;
        backupToDelete.value = null;
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

        <div class="admin-backups">
            <div class="page-header">
                <h1 class="page-title">Database Backups</h1>
                <UButton icon="i-lucide-plus" label="Create Backup" :loading="creating" @click="createBackup" />
            </div>

            <!-- Backups Table -->
            <UCard>
                <UTable :columns="columns" :data="backupsData?.items ?? []" :loading="pending">
                    <template #size-cell="{ row }">
                        {{ formatSize(row.original.size) }}
                    </template>

                    <template #created_at-cell="{ row }">
                        {{ formatDate(row.original.created_at) }}
                    </template>

                    <template #actions-cell="{ row }">
                        <div class="actions">
                            <UTooltip text="Download">
                                <UButton
                                    icon="i-lucide-download"
                                    color="neutral"
                                    variant="ghost"
                                    size="xs"
                                    @click="downloadBackup(row.original.filename)"
                                />
                            </UTooltip>
                            <UTooltip text="Delete">
                                <UButton
                                    icon="i-lucide-trash-2"
                                    color="error"
                                    variant="ghost"
                                    size="xs"
                                    :loading="deleting === row.original.filename"
                                    @click="confirmDelete(row.original.filename)"
                                />
                            </UTooltip>
                        </div>
                    </template>
                </UTable>

                <div class="table-footer">
                    <span class="total-count">{{ backupsData?.total ?? 0 }} backups (max 7 retained)</span>
                </div>
            </UCard>

            <div class="info-text">
                <p>Backups are automatically created daily at 4:00 AM. Only the 7 most recent backups are retained.</p>
            </div>

            <!-- Delete Confirmation Modal -->
            <UModal v-model:open="showDeleteModal">
                <template #content>
                    <UCard>
                        <template #header>
                            <h3 class="modal-title">Delete Backup</h3>
                        </template>
                        <p>Are you sure you want to delete this backup?</p>
                        <p class="filename-text">{{ backupToDelete }}</p>
                        <template #footer>
                            <div class="modal-actions">
                                <UButton
                                    label="Cancel"
                                    color="neutral"
                                    variant="outline"
                                    @click="showDeleteModal = false"
                                />
                                <UButton label="Delete" color="error" :loading="!!deleting" @click="deleteBackup" />
                            </div>
                        </template>
                    </UCard>
                </template>
            </UModal>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.admin-backups {
    @apply max-w-4xl mx-auto;
}

.page-header {
    @apply flex items-center justify-between mb-6;
}

.page-title {
    @apply text-2xl font-semibold text-gray-900 dark:text-gray-100;
}

.actions {
    @apply flex gap-1;
}

.table-footer {
    @apply flex justify-end pt-4;
}

.total-count {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.info-text {
    @apply mt-4 text-sm text-gray-500 dark:text-gray-400;
}

.modal-title {
    @apply text-lg font-semibold text-gray-900 dark:text-gray-100;
}

.filename-text {
    @apply mt-2 font-mono text-sm bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded;
}

.modal-actions {
    @apply flex justify-end gap-2;
}
</style>
