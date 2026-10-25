<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Photos being uploaded, with progress and errors. */
const { t } = useI18n();
const { queue, dismiss } = useCmsMediaUpload();
</script>

<template>
    <ul v-if="queue.length" class="flex flex-col gap-2">
        <li
            v-for="item in queue"
            :key="item.key"
            class="flex items-center gap-3 rounded-lg bg-elevated px-3 py-2 text-sm text-highlighted"
        >
            <UIcon
                :name="item.errorKey ? 'i-lucide-circle-alert' : 'i-lucide-loader-circle'"
                class="size-4 shrink-0"
                :class="item.errorKey ? 'text-error' : 'animate-spin text-primary'"
            />
            <div class="min-w-0 flex-1">
                <p class="truncate">{{ item.name }}</p>
                <p v-if="item.errorKey" class="text-error">{{ t(item.errorKey) }}</p>
                <template v-else>
                    <UProgress :model-value="item.progress * 100" size="xs" class="mt-1" />
                    <p v-if="item.progress === 1" class="text-xs text-muted">{{ t('cms.media.processing') }}</p>
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
</template>
