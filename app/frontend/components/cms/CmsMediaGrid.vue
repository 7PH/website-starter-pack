<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
defineProps<{ items: CmsMediaRead[] }>();
defineEmits<{ select: [media: CmsMediaRead] }>();
const { t } = useI18n();
</script>

<template>
    <ul class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        <li v-for="media in items" :key="media.id">
            <button
                type="button"
                class="group relative block aspect-square w-full overflow-hidden rounded-lg bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 dark:bg-gray-800"
                :title="media.alt || media.original_name"
                @click="$emit('select', media)"
            >
                <CmsImage
                    :media="media"
                    sizes="(min-width: 1024px) 20vw, (min-width: 640px) 33vw, 50vw"
                    class="size-full object-cover transition-transform duration-200 group-hover:scale-105"
                />
                <span
                    v-if="!media.alt"
                    class="absolute bottom-1.5 left-1.5 inline-flex items-center gap-1 rounded bg-black/60 px-1.5 py-0.5 text-xs text-white"
                >
                    <UIcon name="i-lucide-text-cursor-input" class="size-3" />
                    {{ t('cms.media.noAlt') }}
                </span>
            </button>
        </li>
    </ul>
</template>
