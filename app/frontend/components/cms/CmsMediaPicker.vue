<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Modal to pick a photo from the library, or upload a new one first. */
const open = defineModel<boolean>('open', { default: false });
const emit = defineEmits<{ select: [media: CmsMediaRead] }>();

const { t } = useI18n();
const showCmsError = useCmsErrorToast();
const { items, loading, hasMore, load, add } = useCmsMediaLibrary();

// Reload on every open: photos may have been added or deleted elsewhere since.
watch(
    open,
    (isOpen) => {
        if (isOpen) load(true).catch((error) => showCmsError(error));
    },
    { immediate: true },
);

function pick(media: CmsMediaRead) {
    emit('select', media);
    open.value = false;
}
</script>

<template>
    <UModal v-model:open="open" :title="t('cms.media.pickerTitle')" class="sm:max-w-4xl">
        <template #body>
            <div class="flex flex-col gap-4">
                <CmsMediaDropzone compact @uploaded="add" />
                <CmsMediaGrid :items="items" @select="pick" />
                <p v-if="!loading && !items.length" class="py-6 text-center text-sm text-gray-500">
                    {{ t('cms.media.empty') }}
                </p>
                <UButton
                    v-if="hasMore"
                    :label="t('cms.media.loadMore')"
                    :loading="loading"
                    color="neutral"
                    variant="outline"
                    class="self-center"
                    @click="load()"
                />
            </div>
        </template>
    </UModal>
</template>
