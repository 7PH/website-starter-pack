<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
const media = defineModel<CmsMediaRead | null>({ default: null });

const { t } = useI18n();
const api = useApi();
const showCmsError = useCmsErrorToast();
const pickerOpen = ref(false);

function select(picked: CmsMediaRead) {
    media.value = picked;
    pickerOpen.value = false;
}

// Framing belongs to the photo, not to this page: it saves on the photo right away instead of waiting for the page's Save.
// The model isn't updated with the result, or the page would look unsaved for a change already saved.
const focalX = ref(0.5);
const focalY = ref(0.5);
const status = ref<'idle' | 'saving' | 'saved'>('idle');
let saved = { x: 0.5, y: 0.5 };

watch(
    () => media.value?.id,
    () => {
        focalX.value = saved.x = media.value?.focal_x ?? 0.5;
        focalY.value = saved.y = media.value?.focal_y ?? 0.5;
        status.value = 'idle';
    },
    { immediate: true },
);

watchDebounced(
    [focalX, focalY],
    async ([x, y]) => {
        const id = media.value?.id;
        if (!id || (x === saved.x && y === saved.y)) return;
        status.value = 'saving';
        try {
            await api.patch(`/cms/media/${id}`, { focal_x: x, focal_y: y });
            saved = { x, y };
            status.value = 'saved';
        } catch (error) {
            status.value = 'idle';
            showCmsError(error);
        }
    },
    { debounce: 400 },
);
</script>

<template>
    <div class="flex w-full flex-col items-start gap-3">
        <div v-if="media" class="flex w-full flex-col gap-1 sm:max-w-md">
            <CmsFocalEditor v-model:x="focalX" v-model:y="focalY" :media="media" />
            <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ t('cms.media.focalShared') }}
                <span v-if="status !== 'idle'" class="font-medium" aria-live="polite">{{
                    status === 'saving' ? t('cms.media.focalSaving') : t('cms.media.focalSaved')
                }}</span>
            </p>
        </div>
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
