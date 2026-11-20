<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Modal to pick a photo from the library, or upload a new one first. */
const open = defineModel<boolean>('open', { default: false });
const emit = defineEmits<{ select: [media: CmsMediaRead] }>();

const { t } = useI18n();
const showCmsError = useCmsErrorToast();
// Editors changing a photo are almost always after one already on the site.
const filters = ref(defaultCmsMediaFilters('used'));
const { items, folders, loading, failed, hasMore, load, add } = useCmsMediaLibrary(filters);

function reload() {
    load(true).catch((error) => showCmsError(error));
}

// Reload on every open: photos may have been added or deleted elsewhere since.
watch(open, (isOpen) => isOpen && reload(), { immediate: true });
watch(filters, () => open.value && reload());

function pick(media: CmsMediaRead) {
    emit('select', media);
    open.value = false;
}
</script>

<template>
    <UModal v-model:open="open" :title="t('cms.media.pickerTitle')" class="sm:max-w-4xl">
        <template #body>
            <div class="flex flex-col gap-4">
                <CmsMediaDropzone @uploaded="add" />
                <CmsMediaFilterBar v-model="filters" :folders="folders" />
                <CmsMediaGrid :items="items" @select="pick" />
                <p v-if="!loading && !items.length" class="py-6 text-center text-sm text-gray-500">
                    {{
                        filters.q || filters.usage || filters.folder !== null
                            ? t('cms.media.noResults')
                            : t('cms.media.empty')
                    }}
                </p>
                <CmsMediaLoadMore
                    v-if="hasMore"
                    :loading="loading"
                    :paused="failed"
                    @load="load().catch((error) => showCmsError(error))"
                />
            </div>
        </template>
    </UModal>
</template>
