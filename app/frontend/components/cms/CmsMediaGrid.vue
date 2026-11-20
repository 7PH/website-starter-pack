<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
// `captions`: the description (or a prompt to add one) under each photo, for the library page. The default slot goes first in the grid.
// `selected`: set when picking several photos; a click then toggles instead of selecting.
const props = defineProps<{ items: CmsMediaLibraryItem[]; captions?: boolean; selected?: Set<number> }>();
const emit = defineEmits<{ select: [media: CmsMediaLibraryItem]; toggle: [id: number] }>();
const { t } = useI18n();

// Only photos shown on a page need a description: the rest is invisible to visitors.
const needsAlt = (media: CmsMediaLibraryItem) => media.usage_count > 0 && !media.alt;

function click(media: CmsMediaLibraryItem) {
    if (props.selected) emit('toggle', media.id);
    else emit('select', media);
}
</script>

<template>
    <ul class="grid grid-cols-2 gap-3 sm:grid-cols-[repeat(auto-fill,minmax(150px,1fr))]">
        <li v-if="$slots.default"><slot /></li>
        <li v-for="media in items" :key="media.id" class="flex min-w-0 flex-col gap-1.5">
            <button
                type="button"
                class="group relative block aspect-square w-full overflow-hidden rounded-xl bg-elevated focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                :class="{ 'ring-3 ring-primary': selected?.has(media.id) }"
                :title="media.alt || media.original_name"
                :aria-pressed="selected ? selected.has(media.id) : undefined"
                @click="click(media)"
            >
                <!-- Tiles are ~150-250px: the smallest generated width is enough, even on a sharp screen. -->
                <CmsImage
                    :media="media"
                    sizes="240px"
                    class="size-full object-cover transition-transform duration-200 group-hover:scale-105"
                />
                <span
                    v-if="selected"
                    class="absolute top-2 left-2 flex size-5.5 items-center justify-center rounded-md border-2 border-white shadow"
                    :class="selected.has(media.id) ? 'bg-primary' : 'bg-black/30'"
                >
                    <UIcon v-if="selected.has(media.id)" name="i-lucide-check" class="size-3.5 text-white" />
                </span>
                <span
                    v-if="needsAlt(media)"
                    class="absolute top-2 right-2 size-2.5 rounded-full bg-amber-400 ring-2 ring-white dark:ring-gray-900"
                    :title="t('cms.media.noAlt')"
                    :aria-label="t('cms.media.noAlt')"
                    role="img"
                />
                <span
                    v-if="media.usage_count"
                    class="absolute bottom-2 left-2 flex items-center gap-1 rounded-full bg-black/60 px-1.5 py-0.5 text-xs font-medium text-white"
                    :title="t('cms.media.usedCount', media.usage_count)"
                >
                    <UIcon name="i-lucide-file-text" class="size-3" />
                    {{ media.usage_count }}
                </span>
            </button>
            <template v-if="captions">
                <p v-if="media.alt || !needsAlt(media)" class="truncate text-xs text-muted">
                    {{ media.alt || media.original_name }}
                </p>
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
