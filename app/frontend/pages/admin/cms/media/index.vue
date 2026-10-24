<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin', 'cms'],
});

const { t } = useI18n();
const { showError } = useToastHelpers();
const { items, total, loading, hasMore, load, add, replace, remove } = useCmsMediaLibrary();

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
    load(reset).catch((error) => showError(error, 'core.errors.generic'));
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
    <div class="page-box">
        <AdminPageBanner />

        <div class="mx-auto flex max-w-7xl flex-col gap-6">
            <div>
                <div class="flex items-baseline gap-4">
                    <h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ t('cms.media.title') }}</h1>
                    <span class="text-sm text-gray-500 dark:text-gray-400">{{ t('cms.media.count', total) }}</span>
                </div>
                <p class="mt-1 text-gray-600 dark:text-gray-400">{{ t('cms.media.subtitle') }}</p>
            </div>

            <CmsMediaDropzone :compact="items.length > 0" @uploaded="add" />

            <CmsMediaGrid :items="items" @select="select" />

            <p v-if="!loading && !items.length" class="py-6 text-center text-gray-500">{{ t('cms.media.empty') }}</p>

            <UButton
                v-if="hasMore"
                :label="t('cms.media.loadMore')"
                :loading="loading"
                color="neutral"
                variant="outline"
                class="self-center"
                @click="loadMore()"
            />
        </div>

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
                <p class="text-gray-600 dark:text-gray-400">{{ t('cms.media.unsavedMessage') }}</p>
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
