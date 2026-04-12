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
const restoring = ref<string | null>(null);
const showDeleteModal = ref(false);
const backupToDelete = ref<string | null>(null);
const restoreStep = ref<0 | 1 | 2>(0); // 0=closed, 1=warning, 2=type-to-confirm
const backupToRestore = ref<string | null>(null);
const restoreConfirmInput = ref('');

// Table columns
const columns = [
    { accessorKey: 'comment', header: 'Type' },
    { accessorKey: 'size', header: 'Size' },
    { accessorKey: 'created_at', header: 'Created' },
    { accessorKey: 'actions', header: '' },
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

function confirmRestore(filename: string) {
    backupToRestore.value = filename;
    restoreConfirmInput.value = '';
    restoreStep.value = 1;
}

function proceedToStep2() {
    restoreStep.value = 2;
    restoreConfirmInput.value = '';
}

function cancelRestore() {
    restoreStep.value = 0;
    backupToRestore.value = null;
    restoreConfirmInput.value = '';
}

const restoreConfirmMatch = computed(() => restoreConfirmInput.value === backupToRestore.value);

async function executeRestore() {
    if (!backupToRestore.value || !restoreConfirmMatch.value) return;

    restoring.value = backupToRestore.value;
    try {
        const safetyBackup = await api.post<BackupInfo>(`/admin/backups/${backupToRestore.value}/restore`, {
            confirm_filename: backupToRestore.value,
        });
        toast.add({
            title: 'Database restored',
            description: `Safety backup created: ${safetyBackup.filename}`,
            color: 'success',
            duration: 8000,
        });
        refresh();
    } catch {
        toast.add({
            title: 'Restore failed',
            description: 'Failed to restore database from backup',
            color: 'error',
            duration: 5000,
        });
    } finally {
        restoring.value = null;
        cancelRestore();
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
                    <template #comment-cell="{ row }">
                        <div class="type-cell">
                            <span v-if="row.original.comment">{{ row.original.comment }}</span>
                            <span v-else class="type-cell--empty">&mdash;</span>
                            <UTooltip :text="row.original.filename">
                                <UIcon name="i-lucide-info" class="type-cell-info" />
                            </UTooltip>
                        </div>
                    </template>

                    <template #size-cell="{ row }">
                        {{ formatSize(row.original.size) }}
                    </template>

                    <template #created_at-cell="{ row }">
                        {{ formatDate(row.original.created_at) }}
                    </template>

                    <template #actions-cell="{ row }">
                        <div class="actions">
                            <UTooltip text="Restore">
                                <UButton
                                    icon="i-lucide-database"
                                    color="warning"
                                    variant="ghost"
                                    size="xs"
                                    :loading="restoring === row.original.filename"
                                    @click="confirmRestore(row.original.filename)"
                                />
                            </UTooltip>
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

            <!-- Restore Step 1: Warning -->
            <UModal
                :open="restoreStep === 1"
                @update:open="
                    (v: boolean) => {
                        if (!v) cancelRestore();
                    }
                "
            >
                <template #content>
                    <UCard>
                        <template #header>
                            <h3 class="modal-title modal-title--danger">Restore Database</h3>
                        </template>
                        <div class="restore-warning">
                            <p class="restore-warning-text">
                                This will <strong>drop all existing tables</strong> and replace the database with the
                                contents of this backup. This action is destructive and cannot be undone.
                            </p>
                            <p class="filename-text">{{ backupToRestore }}</p>
                            <p class="restore-safety-note">
                                A safety backup of the current database will be created automatically before restoring.
                            </p>
                        </div>
                        <template #footer>
                            <div class="modal-actions">
                                <UButton label="Cancel" color="neutral" variant="outline" @click="cancelRestore" />
                                <UButton label="Continue" color="error" @click="proceedToStep2" />
                            </div>
                        </template>
                    </UCard>
                </template>
            </UModal>

            <!-- Restore Step 2: Type to confirm -->
            <UModal
                :open="restoreStep === 2"
                @update:open="
                    (v: boolean) => {
                        if (!v) cancelRestore();
                    }
                "
            >
                <template #content>
                    <UCard>
                        <template #header>
                            <h3 class="modal-title modal-title--danger">Confirm Restore</h3>
                        </template>
                        <div class="restore-confirm">
                            <p>Type the backup filename to confirm:</p>
                            <p class="filename-text">{{ backupToRestore }}</p>
                            <UInput
                                v-model="restoreConfirmInput"
                                placeholder="Type filename here"
                                class="restore-confirm-input"
                            />
                        </div>
                        <template #footer>
                            <div class="modal-actions">
                                <UButton label="Cancel" color="neutral" variant="outline" @click="cancelRestore" />
                                <UButton
                                    label="Restore"
                                    color="error"
                                    :disabled="!restoreConfirmMatch"
                                    :loading="!!restoring"
                                    @click="executeRestore"
                                />
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

.modal-title--danger {
    @apply text-red-600 dark:text-red-400;
}

.restore-warning-text {
    @apply text-gray-600 dark:text-gray-400;
}

.restore-safety-note {
    @apply mt-3 text-sm text-gray-500 dark:text-gray-400 italic;
}

.restore-confirm {
    @apply space-y-3;
}

.restore-confirm-input {
    @apply mt-2;
}

.type-cell {
    @apply flex items-center gap-1.5 text-sm;
}

.type-cell--empty {
    @apply text-gray-400 dark:text-gray-600;
}

.type-cell-info {
    @apply text-gray-400 dark:text-gray-500 size-3.5 shrink-0 cursor-help;
}
</style>
