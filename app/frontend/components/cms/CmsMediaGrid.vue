<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
// `captions`: the description (or a prompt to add one) under each photo, for the library page. The default slot goes first in the grid.
defineProps<{ items: CmsMediaRead[]; captions?: boolean }>();
defineEmits<{ select: [media: CmsMediaRead] }>();
const { t } = useI18n();
</script>

<template>
    <ul class="grid grid-cols-2 gap-3 sm:grid-cols-[repeat(auto-fill,minmax(150px,1fr))]">
        <li v-if="$slots.default"><slot /></li>
        <li v-for="media in items" :key="media.id" class="flex min-w-0 flex-col gap-1.5">
            <button
                type="button"
                class="group relative block aspect-square w-full overflow-hidden rounded-xl bg-elevated focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
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
                    class="absolute top-2 right-2 flex size-5.5 items-center justify-center rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                    :title="t('cms.media.noAlt')"
                >
                    <UIcon name="i-lucide-triangle-alert" class="size-3" />
                </span>
            </button>
            <template v-if="captions">
                <p v-if="media.alt" class="truncate text-xs text-muted">{{ media.alt }}</p>
                <button
                    v-else
                    type="button"
                    class="flex items-center gap-1.5 text-left text-xs font-bold text-muted hover:text-primary"
                    @click="$emit('select', media)"
                >
                    <UIcon name="i-lucide-pencil" class="size-3 shrink-0" />
                    {{ t('cms.media.addAlt') }}
                </button>
            </template>
        </li>
    </ul>
</template>
