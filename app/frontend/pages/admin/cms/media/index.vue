<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin', 'cms'],
});

const { t } = useI18n();
const showCmsError = useCmsErrorToast();
const { items, total, loading, hasMore, load, add, replace, remove } = useCmsMediaLibrary();

const dropzone = useTemplateRef<{ pick: () => void }>('dropzone');

// Counts loaded photos only: the library loads 60 at a time and the API has no filter on descriptions.
const missingAlt = computed(() => items.value.filter((m) => !m.alt).length);
const onlyMissing = ref(false);
watch(missingAlt, (count) => {
    if (!count) onlyMissing.value = false;
});
const shown = computed(() => (onlyMissing.value ? items.value.filter((m) => !m.alt) : items.value));

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

function onUpdated(media: CmsMediaRead) {
    replace(media);
    selected.value = media;
}

function onDeleted(id: number) {
    remove(id);
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
            v-if="missingAlt"
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
                    onClick: () => (onlyMissing = !onlyMissing),
                },
            ]"
        />

        <CmsMediaUploadQueue />

        <CmsMediaGrid :items="shown" captions @select="select">
            <CmsMediaDropzone ref="dropzone" tile @uploaded="add" />
        </CmsMediaGrid>

        <UButton
            v-if="hasMore"
            :label="t('cms.media.loadMore')"
            :loading="loading"
            color="neutral"
            variant="outline"
            class="self-center"
            @click="loadMore()"
        />

        <USlideover v-model:open="panelOpen" :title="t('cms.media.details')">
            <template #body>
                <CmsMediaDetails
                    v-if="selected"
                    ref="details"
                    :media="selected"
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
