<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/**
 * Drag & drop (or pick) photos, upload them with progress. Emits each photo once processed.
 * `tile`: a square to put first in a CmsMediaGrid, the page shows <CmsMediaUploadQueue /> itself. `pick()` opens the file dialog.
 */
defineProps<{ tile?: boolean }>();
const emit = defineEmits<{ uploaded: [media: CmsMediaRead] }>();

const { t } = useI18n();
const { enqueue } = useCmsMediaUpload((media) => emit('uploaded', media));
const input = ref<HTMLInputElement>();
const dragging = ref(false);

function onDrop(event: DragEvent) {
    dragging.value = false;
    enqueue(Array.from(event.dataTransfer?.files ?? []));
}

function onPick() {
    enqueue(Array.from(input.value?.files ?? []));
    // Reset so picking the same file again still fires `change`.
    input.value!.value = '';
}

const pick = () => input.value?.click();
defineExpose({ pick });
</script>

<template>
    <!-- A label opens its file input natively; the input stays focusable for keyboards. -->
    <label
        v-if="tile"
        class="flex aspect-square w-full cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-3 text-center transition-colors focus-within:ring-2 focus-within:ring-primary hover:border-primary hover:text-highlighted"
        :class="
            dragging
                ? 'border-primary bg-primary-50 text-highlighted dark:bg-primary-950/40'
                : 'border-default text-muted'
        "
        @dragenter.prevent="dragging = true"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
    >
        <UIcon name="i-lucide-image-plus" class="size-7" />
        <!-- Nothing to drag from a phone. -->
        <span class="text-[13px] font-bold sm:hidden">{{ t('cms.media.choose') }}</span>
        <span class="hidden text-[13px] font-bold sm:block">{{ t('cms.media.dropTitle') }}</span>
        <span class="text-[11px] text-dimmed">{{ t('cms.media.dropHintShort') }}</span>
        <input ref="input" type="file" :accept="CMS_MEDIA_ACCEPT" multiple class="sr-only" @change="onPick" />
    </label>

    <div v-else class="flex flex-col gap-3">
        <div
            class="flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-4 text-center transition-colors"
            :class="dragging ? 'border-primary bg-primary-50 dark:bg-primary-950/40' : 'border-default'"
            @dragenter.prevent="dragging = true"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @drop.prevent="onDrop"
        >
            <!-- Hidden on phones: there is nothing to drag from there. -->
            <p class="hidden text-sm text-toned sm:block">{{ t('cms.media.dropTitle') }} {{ t('cms.media.dropOr') }}</p>
            <UButton :label="t('cms.media.choose')" icon="i-lucide-upload" @click="pick" />
            <p class="text-xs text-muted">{{ t('cms.media.dropHint') }}</p>
            <input ref="input" type="file" :accept="CMS_MEDIA_ACCEPT" multiple class="hidden" @change="onPick" />
        </div>
        <CmsMediaUploadQueue />
    </div>
</template>
