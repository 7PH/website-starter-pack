<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Focal point picker with its hint and crop previews. Saving is the caller's job. */
const props = defineProps<{ media: CmsMediaRead }>();
const x = defineModel<number>('x', { required: true });
const y = defineModel<number>('y', { required: true });

const { t } = useI18n();
// Crop previews follow the marker before saving.
const preview = computed(() => ({ ...props.media, focal_x: x.value, focal_y: y.value }));
</script>

<template>
    <div class="flex flex-col gap-2">
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('cms.media.focalHelp') }}</p>
        <CmsFocalPicker v-model:x="x" v-model:y="y" :media="media" />
        <div class="flex flex-wrap items-end gap-3">
            <figure class="w-16 shrink-0">
                <CmsImage :media="preview" sizes="64px" class="aspect-[9/16] w-full rounded object-cover" />
                <figcaption class="mt-1 text-xs text-gray-500">{{ t('cms.media.previewPortrait') }}</figcaption>
            </figure>
            <figure class="w-24 shrink-0">
                <CmsImage :media="preview" sizes="96px" class="aspect-square w-full rounded object-cover" />
                <figcaption class="mt-1 text-xs text-gray-500">{{ t('cms.media.previewSquare') }}</figcaption>
            </figure>
            <figure class="min-w-48 flex-1">
                <CmsImage :media="preview" sizes="320px" class="aspect-[21/9] w-full rounded object-cover" />
                <figcaption class="mt-1 text-xs text-gray-500">{{ t('cms.media.previewWide') }}</figcaption>
            </figure>
        </div>
    </div>
</template>
