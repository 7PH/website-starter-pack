<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin', 'cms'],
});

const { t } = useI18n();
const api = useApi();
const modal = useModalStore();
const { showSuccess, showWarning } = useToastHelpers();
const showCmsError = useCmsErrorToast();
const filters = ref(defaultCmsMediaFilters());
const { items, total, missingAlt, folders, loading, failed, hasMore, load, add, replace, remove } =
    useCmsMediaLibrary(filters);

const dropzone = useTemplateRef<{ pick: () => void }>('dropzone');
const filtered = computed(() => !!(filters.value.q || filters.value.usage || filters.value.folder !== null));
const onlyMissing = computed(() => filters.value.usage === 'missing_alt');
const toggleMissing = () => (filters.value = { ...filters.value, usage: onlyMissing.value ? '' : 'missing_alt' });

// Several photos picked for a bulk action. null: not selecting, a click opens the photo.
const selection = ref<Set<number> | null>(null);
const busy = ref(false);
const folderTarget = ref('');

function toggle(id: number) {
    const next = new Set(selection.value);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selection.value = next;
}

async function selectUnused() {
    // "Used" filters show no unused photo.
    if (filters.value.usage === 'used' || filters.value.usage === 'missing_alt') return;
    try {
        const ids = await api.get<number[]>('/cms/media/ids', { ...cmsMediaParams(filters.value), usage: 'unused' });
        selection.value = new Set([...(selection.value ?? []), ...ids]);
    } catch (error) {
        showCmsError(error);
    }
}

async function bulkDelete() {
    const ids = [...(selection.value ?? [])];
    const confirmed = await modal.open<boolean>('confirm', {
        title: t('cms.media.bulkDeleteTitle', ids.length),
        message: t('cms.media.bulkDeleteMessage'),
        confirmText: t('cms.media.delete'),
        confirmColor: 'error',
        icon: 'i-lucide-trash-2',
    });
    if (!confirmed) return;
    busy.value = true;
    try {
        const result = await api.post<CmsMediaBulkDeleteResponse>('/cms/media/bulk-delete', { ids });
        remove(result.deleted);
        if (result.deleted.length) showSuccess(t('cms.media.bulkDeleted', result.deleted.length));
        if (result.in_use.length) showWarning(t('cms.media.bulkInUse', result.in_use.length));
        selection.value = result.in_use.length ? new Set(result.in_use) : null;
    } catch (error) {
        showCmsError(error);
    } finally {
        busy.value = false;
    }
}

async function bulkMove() {
    busy.value = true;
    try {
        await api.post('/cms/media/bulk-update', { ids: [...(selection.value ?? [])], folder: folderTarget.value });
        showSuccess(t('cms.media.moved'));
        selection.value = null;
        folderTarget.value = '';
        loadMore(true);
    } catch (error) {
        showCmsError(error);
    } finally {
        busy.value = false;
    }
}

const selected = ref<CmsMediaRead | null>(null);
const details = ref<{ dirty: boolean; save: () => Promise<boolean> } | null>(null);
// Leaving the page. Closing the panel or switching photo asks below instead, with a save option.
useUnsavedChangesWarning(() => details.value?.dirty ?? false);

type UnsavedChoice = 'save' | 'discard' | 'cancel';
const unsavedOpen = ref(false);
let answerUnsaved: (choice: UnsavedChoice) => void = () => {};

function askUnsaved(): Promise<UnsavedChoice> {
    unsavedOpen.value = true;
    return new Promise((resolve) => {
        answerUnsaved = (choice) => {
            unsavedOpen.value = false;
            resolve(choice);
        };
    });
}

async function select(media: CmsMediaRead | null) {
    if (media?.id === selected.value?.id) return;
    if (details.value?.dirty) {
        const choice = await askUnsaved();
        if (choice === 'cancel' || (choice === 'save' && !(await details.value.save()))) return;
    }
    selected.value = media;
}

const panelOpen = computed({
    get: () => selected.value !== null,
    set: (open: boolean) => {
        if (!open) void select(null);
    },
});

function loadMore(reset = false) {
    load(reset).catch((error) => showCmsError(error));
}

onMounted(() => loadMore(true));
watch(filters, () => loadMore(true));

function onUpdated(media: CmsMediaRead) {
    replace(media);
    selected.value = media;
}

function onDeleted(id: number) {
    remove([id]);
    selected.value = null;
}
</script>

<template>
    <div class="flex flex-col gap-4.5">
        <AdminPageHeader :title="t('cms.media.title')" :count="total" :description="t('cms.media.subtitle')">
            <template #actions>
                <UButton :label="t('cms.media.choose')" icon="i-lucide-upload" size="lg" @click="dropzone?.pick()" />
            </template>
        </AdminPageHeader>

        <UAlert
            v-if="missingAlt || onlyMissing"
            color="warning"
            variant="subtle"
            icon="i-lucide-text-cursor-input"
            :title="t('cms.media.missingAlt', missingAlt)"
            orientation="horizontal"
            :actions="[
                {
                    label: onlyMissing ? t('cms.media.showAll') : t('cms.media.showMissing'),
                    color: 'warning',
                    variant: 'outline',
                    onClick: toggleMissing,
                },
            ]"
        />

        <CmsMediaUploadQueue />

        <div class="flex flex-wrap items-center justify-between gap-2">
            <CmsMediaFilterBar v-model="filters" :folders="folders" />
            <UButton
                v-if="!selection"
                :label="t('cms.media.select')"
                icon="i-lucide-square-check"
                color="neutral"
                variant="outline"
                @click="selection = new Set()"
            />
        </div>

        <div
            v-if="selection"
            class="sticky top-2 z-10 flex flex-wrap items-center gap-2 rounded-xl border border-default bg-default p-2 shadow-sm"
        >
            <span class="px-2 text-sm font-medium">{{ t('cms.media.selected', selection.size) }}</span>
            <UButton
                v-if="filters.usage !== 'used' && filters.usage !== 'missing_alt'"
                :label="t('cms.media.selectUnused')"
                color="neutral"
                variant="ghost"
                @click="selectUnused"
            />
            <div class="flex items-center gap-1">
                <UInput
                    v-model="folderTarget"
                    :placeholder="t('cms.media.folderNone')"
                    :aria-label="t('cms.media.folder')"
                    list="cms-media-bulk-folders"
                    icon="i-lucide-folder"
                    class="w-40"
                />
                <datalist id="cms-media-bulk-folders">
                    <option v-for="f in folders" :key="f" :value="f" />
                </datalist>
                <UButton
                    :label="t('cms.media.moveToFolder')"
                    color="neutral"
                    variant="outline"
                    :disabled="!selection.size"
                    :loading="busy"
                    @click="bulkMove"
                />
            </div>
            <UButton
                :label="t('cms.media.delete')"
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                :disabled="!selection.size"
                :loading="busy"
                @click="bulkDelete"
            />
            <UButton
                :label="t('core.common.cancel')"
                color="neutral"
                variant="ghost"
                class="ms-auto"
                @click="selection = null"
            />
        </div>

        <CmsMediaGrid :items="items" captions :selected="selection ?? undefined" @select="select" @toggle="toggle">
            <CmsMediaDropzone ref="dropzone" tile @uploaded="add" />
        </CmsMediaGrid>

        <p v-if="!loading && !items.length && filtered" class="py-6 text-center text-sm text-muted">
            {{ t('cms.media.noResults') }}
        </p>

        <CmsMediaLoadMore v-if="hasMore" :loading="loading" :paused="failed" @load="loadMore()" />

        <USlideover v-model:open="panelOpen" :title="t('cms.media.details')">
            <template #body>
                <CmsMediaDetails
                    v-if="selected"
                    ref="details"
                    :media="selected"
                    :folders="folders"
                    @updated="onUpdated"
                    @deleted="onDeleted"
                />
            </template>
        </USlideover>

        <UModal
            :open="unsavedOpen"
            :title="t('cms.media.unsavedTitle')"
            class="sm:max-w-md"
            @update:open="(open: boolean) => !open && answerUnsaved('cancel')"
        >
            <template #body>
                <p class="text-muted">{{ t('cms.media.unsavedMessage') }}</p>
            </template>
            <template #footer>
                <div class="flex w-full flex-wrap justify-end gap-3">
                    <UButton
                        :label="t('core.common.cancel')"
                        color="neutral"
                        variant="ghost"
                        @click="answerUnsaved('cancel')"
                    />
                    <UButton
                        :label="t('cms.media.discard')"
                        color="neutral"
                        variant="outline"
                        @click="answerUnsaved('discard')"
                    />
                    <UButton :label="t('cms.media.save')" @click="answerUnsaved('save')" />
                </div>
            </template>
        </UModal>
    </div>
</template>
