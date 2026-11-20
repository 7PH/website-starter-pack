<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Search, sort, usage and folder filters of the photo library, shared by the library page and the picker. */
const filters = defineModel<CmsMediaFilters>({ required: true });
defineProps<{ folders: string[] }>();

const { t } = useI18n();

// Typing shouldn't send a request per key.
const search = ref(filters.value.q);
watchDebounced(search, (q) => (filters.value = { ...filters.value, q }), { debounce: 300 });
watch(
    () => filters.value.q,
    (q) => (search.value = q),
);

const set = (patch: Partial<CmsMediaFilters>) => (filters.value = { ...filters.value, ...patch });

const sortItems = computed(() => [
    { label: t('cms.media.sortUsed'), value: 'used' },
    { label: t('cms.media.sortNewest'), value: 'newest' },
    { label: t('cms.media.sortOldest'), value: 'oldest' },
    { label: t('cms.media.sortName'), value: 'name' },
]);
// Select items can't hold '' or null as a value.
const usageItems = computed(() => [
    { label: t('cms.media.filterAll'), value: 'all' },
    { label: t('cms.media.filterUsed'), value: 'used' },
    { label: t('cms.media.filterUnused'), value: 'unused' },
    { label: t('cms.media.filterMissingAlt'), value: 'missing_alt' },
]);
const NO_FOLDER = '\u0000none';
const ALL_FOLDERS = '\u0000all';
</script>

<template>
    <div class="flex flex-wrap gap-2">
        <UInput
            v-model="search"
            icon="i-lucide-search"
            :placeholder="t('cms.media.search')"
            :aria-label="t('cms.media.search')"
            type="search"
            class="w-full sm:w-64"
        />
        <USelect
            :model-value="filters.sort"
            :items="sortItems"
            :aria-label="t('cms.media.sort')"
            class="w-full sm:w-auto"
            @update:model-value="(sort) => set({ sort: sort as CmsMediaSort })"
        />
        <USelect
            :model-value="filters.usage || 'all'"
            :items="usageItems"
            :aria-label="t('cms.media.filterLabel')"
            class="w-full sm:w-auto"
            @update:model-value="(v) => set({ usage: v === 'all' ? '' : (v as CmsMediaUsageFilter) })"
        />
        <USelect
            v-if="folders.length || filters.folder !== null"
            :model-value="filters.folder === null ? ALL_FOLDERS : filters.folder || NO_FOLDER"
            :items="[
                { label: t('cms.media.folderAll'), value: ALL_FOLDERS },
                { label: t('cms.media.folderNone'), value: NO_FOLDER },
                ...folders.map((f) => ({ label: f, value: f })),
            ]"
            :aria-label="t('cms.media.folder')"
            icon="i-lucide-folder"
            class="w-full sm:w-auto"
            @update:model-value="(v) => set({ folder: v === ALL_FOLDERS ? null : v === NO_FOLDER ? '' : v })"
        />
    </div>
</template>
