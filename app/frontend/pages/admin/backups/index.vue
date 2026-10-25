<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin'],
});

const api = useApi();
const auth = useAuth();
const { showSuccess, showError } = useToastHelpers();

const creating = ref(false);
const deleting = ref<string | null>(null);
const restoring = ref<string | null>(null);
const showDeleteModal = ref(false);
const backupToDelete = ref<string | null>(null);
const restoreStep = ref<0 | 1 | 2>(0); // 0=closed, 1=warning, 2=type-to-confirm
const backupToRestore = ref<string | null>(null);
const restoreConfirmInput = ref('');

// Mirrors MAX_BACKUPS in the backend
const MAX_BACKUPS = 7;

// Keyed by the comment the backend derives from the filename tag
const TYPES: Record<string, { label: string; icon: string; tile: string }> = {
    'Pre-restore backup': {
        label: 'Pre-restore snapshot',
        icon: 'i-lucide-history',
        tile: 'bg-warning/10 text-warning',
    },
    'Manual backup': {
        label: 'Manual backup',
        icon: 'i-lucide-hand',
        tile: 'bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-300',
    },
    'Automatic backup': { label: 'Automatic backup', icon: 'i-lucide-clock', tile: 'bg-elevated text-muted' },
};

function backupType(comment: string | null | undefined) {
    return (
        TYPES[comment ?? ''] ?? {
            label: comment || 'Unlabeled backup',
            icon: 'i-lucide-database',
            tile: 'bg-elevated text-muted',
        }
    );
}

function formatCreated(dateStr: string): string {
    const d = new Date(dateStr);
    const date = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    return `${date} · ${d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
}

const {
    data: backupsData,
    pending,
    refresh,
} = await useAsyncData<BackupListResponse>('admin-backups', () => api.get('/admin/backups'), { server: false });

function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

async function createBackup() {
    creating.value = true;
    try {
        await api.post('/admin/backups');
        showSuccess('Backup created', 'Database backup completed successfully');
        refresh();
    } catch (error) {
        showError(error, 'core.errors.generic');
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
    } catch (error) {
        showError(error, 'core.errors.generic');
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
        showSuccess('Backup deleted', 'Backup file removed successfully');
        refresh();
    } catch (error) {
        showError(error, 'core.errors.generic');
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
const restoreHasMedia = computed(
    () => !!backupsData.value?.items.find((b) => b.filename === backupToRestore.value)?.media_filename,
);

async function executeRestore() {
    if (!backupToRestore.value || !restoreConfirmMatch.value) return;

    restoring.value = backupToRestore.value;
    try {
        const safetyBackup = await api.post<BackupInfo>(`/admin/backups/${backupToRestore.value}/restore`, {
            confirm_filename: backupToRestore.value,
        });
        showSuccess('Database restored', `Safety backup created: ${safetyBackup.filename}`);
        refresh();
    } catch (error) {
        showError(error, 'core.errors.generic');
    } finally {
        restoring.value = null;
        cancelRestore();
    }
}
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader
            title="Backups"
            :description="`Created automatically every day at 4:00 AM. The ${MAX_BACKUPS} most recent are kept.`"
        >
            <template #actions>
                <UButton
                    icon="i-lucide-plus"
                    label="Create backup"
                    size="lg"
                    :loading="creating"
                    @click="createBackup"
                />
            </template>
        </AdminPageHeader>

        <div
            v-if="backupsData"
            class="flex flex-wrap items-center gap-3.5 rounded-xl border border-default bg-default px-4.5 py-3.5"
        >
            <div class="flex min-w-40 flex-1 flex-col gap-0.5">
                <span class="text-[13px] text-muted">Latest backup</span>
                <span class="text-[15px] font-extrabold text-highlighted">
                    {{ backupsData.items[0] ? formatCreated(backupsData.items[0].created_at) : 'None yet' }}
                </span>
            </div>
            <div class="flex min-w-45 flex-col gap-1.5">
                <span class="text-[13px] text-muted">
                    Retention · {{ Math.min(backupsData.total, MAX_BACKUPS) }} of {{ MAX_BACKUPS }} slots used
                </span>
                <div class="flex gap-0.75">
                    <span
                        v-for="i in MAX_BACKUPS"
                        :key="i"
                        class="h-1.5 w-5.5 rounded-[3px]"
                        :class="i <= backupsData.total ? 'bg-primary' : 'bg-elevated'"
                    />
                </div>
            </div>
        </div>

        <AdminCard>
            <div
                v-for="b in backupsData?.items ?? []"
                :key="b.filename"
                class="flex flex-wrap items-center gap-3.5 px-4.5 py-3"
            >
                <span
                    class="flex size-8.5 shrink-0 items-center justify-center rounded-[9px]"
                    :class="backupType(b.comment).tile"
                >
                    <UIcon :name="backupType(b.comment).icon" class="size-4" />
                </span>
                <div class="flex min-w-40 flex-1 flex-col gap-px" :title="b.filename">
                    <span class="text-sm font-bold text-highlighted">{{ backupType(b.comment).label }}</span>
                    <span class="text-[13px] text-muted"
                        >{{ formatCreated(b.created_at) }} · {{ formatSize(b.size) }}</span
                    >
                </div>
                <div class="flex items-center gap-1">
                    <UButton
                        label="Restore"
                        color="neutral"
                        variant="outline"
                        :loading="restoring === b.filename"
                        @click="confirmRestore(b.filename)"
                    />
                    <UTooltip text="Download">
                        <UButton
                            icon="i-lucide-download"
                            color="neutral"
                            variant="ghost"
                            aria-label="Download"
                            @click="downloadBackup(b.filename)"
                        />
                    </UTooltip>
                    <UTooltip v-if="b.media_filename" :text="`Download CMS photos (${formatSize(b.media_size ?? 0)})`">
                        <UButton
                            icon="i-lucide-images"
                            color="neutral"
                            variant="ghost"
                            :aria-label="`Download CMS photos (${formatSize(b.media_size ?? 0)})`"
                            @click="downloadBackup(b.media_filename)"
                        />
                    </UTooltip>
                    <UTooltip text="Delete">
                        <UButton
                            icon="i-lucide-trash-2"
                            color="neutral"
                            variant="ghost"
                            aria-label="Delete"
                            class="hover:bg-error/10 hover:text-error"
                            :loading="deleting === b.filename"
                            @click="confirmDelete(b.filename)"
                        />
                    </UTooltip>
                </div>
            </div>
            <p v-if="pending && !backupsData" class="px-4.5 py-8 text-center text-sm text-muted">Loading…</p>
            <p v-else-if="!backupsData?.items.length" class="px-4.5 py-8 text-center text-sm text-muted">
                No backups yet.
            </p>
        </AdminCard>

        <!-- Delete Confirmation Modal -->
        <UModal v-model:open="showDeleteModal">
            <template #content>
                <UCard>
                    <template #header>
                        <h3 class="text-lg font-semibold text-highlighted">Delete backup</h3>
                    </template>
                    <p>Are you sure you want to delete this backup?</p>
                    <p class="mt-2 rounded bg-elevated px-2 py-1 font-mono text-sm">{{ backupToDelete }}</p>
                    <template #footer>
                        <div class="flex justify-end gap-2">
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
                        <h3 class="text-lg font-semibold text-error">Restore database</h3>
                    </template>
                    <p class="text-muted">
                        This will <strong>drop all existing tables</strong> and replace the database with the contents
                        of this backup.
                    </p>
                    <p class="mt-2 rounded bg-elevated px-2 py-1 font-mono text-sm">{{ backupToRestore }}</p>
                    <p class="mt-3 text-sm text-muted italic">
                        A safety backup of the current data is made first, so you can go back.
                    </p>
                    <p v-if="restoreHasMedia" class="mt-3 text-sm text-muted italic">
                        The CMS photos saved with this backup will replace the current ones.
                    </p>
                    <template #footer>
                        <div class="flex justify-end gap-2">
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
                        <h3 class="text-lg font-semibold text-error">Confirm restore</h3>
                    </template>
                    <div class="flex flex-col gap-3">
                        <p>Type the backup filename to confirm:</p>
                        <p class="rounded bg-elevated px-2 py-1 font-mono text-sm">{{ backupToRestore }}</p>
                        <UInput v-model="restoreConfirmInput" placeholder="Type filename here" />
                    </div>
                    <template #footer>
                        <div class="flex justify-end gap-2">
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
</template>
