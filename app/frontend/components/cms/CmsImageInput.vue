<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
const media = defineModel<CmsMediaRead | null>({ default: null });

const { t } = useI18n();
const pickerOpen = ref(false);

function select(picked: CmsMediaRead) {
    media.value = picked;
    pickerOpen.value = false;
}
</script>

<template>
    <div class="flex flex-col items-start gap-3">
        <CmsImage
            v-if="media"
            :media="media"
            sizes="384px"
            class="w-full max-w-sm aspect-video object-cover rounded-lg"
        />
        <div
            v-else
            class="w-full max-w-sm aspect-video rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 flex items-center justify-center px-4 text-center text-sm text-gray-500"
        >
            {{ t('cms.pages.image.none') }}
        </div>
        <div class="flex flex-wrap gap-2">
            <UButton
                :label="media ? t('cms.pages.image.change') : t('cms.pages.image.choose')"
                icon="i-lucide-image"
                color="neutral"
                variant="outline"
                @click="pickerOpen = true"
            />
            <UButton
                v-if="media"
                :label="t('cms.pages.image.remove')"
                icon="i-lucide-x"
                color="neutral"
                variant="ghost"
                @click="media = null"
            />
        </div>
        <CmsMediaPicker v-model:open="pickerOpen" @select="select" />
    </div>
</template>
