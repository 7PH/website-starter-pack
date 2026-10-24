<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Drag & drop (or pick) photos, upload them with progress. Emits each photo once processed. */
defineProps<{ compact?: boolean }>();
const emit = defineEmits<{ uploaded: [media: CmsMediaRead] }>();

const { t } = useI18n();
const { queue, enqueue, dismiss } = useCmsMediaUpload((media) => emit('uploaded', media));
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
</script>

<template>
    <div class="flex flex-col gap-3">
        <div
            class="flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed text-center transition-colors"
            :class="[
                compact ? 'p-4' : 'p-10',
                dragging
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/40'
                    : 'border-gray-300 dark:border-gray-700',
            ]"
            @dragenter.prevent="dragging = true"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @drop.prevent="onDrop"
        >
            <UIcon v-if="!compact" name="i-lucide-image-plus" class="size-10 text-gray-400" />
            <!-- Hidden on phones: there is nothing to drag from there. -->
            <p class="hidden text-sm text-gray-700 sm:block dark:text-gray-300">
                {{ t('cms.media.dropTitle') }} {{ t('cms.media.dropOr') }}
            </p>
            <UButton :label="t('cms.media.choose')" icon="i-lucide-upload" @click="input?.click()" />
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ t('cms.media.dropHint') }}</p>
            <input ref="input" type="file" :accept="CMS_MEDIA_ACCEPT" multiple class="hidden" @change="onPick" />
        </div>

        <ul v-if="queue.length" class="flex flex-col gap-2">
            <li
                v-for="item in queue"
                :key="item.key"
                class="flex items-center gap-3 rounded-lg bg-gray-50 px-3 py-2 text-sm dark:bg-gray-900"
            >
                <UIcon
                    :name="item.errorKey ? 'i-lucide-circle-alert' : 'i-lucide-loader-circle'"
                    class="size-4 shrink-0"
                    :class="item.errorKey ? 'text-error-500' : 'animate-spin text-primary-500'"
                />
                <div class="min-w-0 flex-1">
                    <p class="truncate">{{ item.name }}</p>
                    <p v-if="item.errorKey" class="text-error-600 dark:text-error-400">{{ t(item.errorKey) }}</p>
                    <template v-else>
                        <UProgress :model-value="item.progress * 100" size="xs" class="mt-1" />
                        <p v-if="item.progress === 1" class="text-xs text-gray-500">{{ t('cms.media.processing') }}</p>
                    </template>
                </div>
                <UButton
                    v-if="item.errorKey"
                    icon="i-lucide-x"
                    color="neutral"
                    variant="ghost"
                    size="xs"
                    :aria-label="t('cms.media.dismiss')"
                    @click="dismiss(item.key)"
                />
            </li>
        </ul>
    </div>
</template>
