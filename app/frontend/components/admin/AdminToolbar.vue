<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Row above a list: search input (with v-model:search), segmented filter (with v-model:segment), then the default slot for extra controls.
defineProps<{
    segments?: { value: string; label: string; count?: number }[];
    searchPlaceholder?: string;
}>();

const search = defineModel<string>('search');
const segment = defineModel<string>('segment');
</script>

<template>
    <div class="flex flex-wrap items-center gap-2.5">
        <UInput
            v-if="search !== undefined"
            v-model="search"
            icon="i-lucide-search"
            size="lg"
            :placeholder="searchPlaceholder ?? 'Search'"
            class="w-full sm:max-w-[340px]"
        />
        <div v-if="segments?.length" class="flex gap-0.5 rounded-[9px] border border-default bg-default p-[3px]">
            <button
                v-for="s in segments"
                :key="s.value"
                type="button"
                :aria-pressed="s.value === segment"
                class="flex h-7.5 items-center gap-1.5 rounded-md px-3 text-[13px] font-bold transition-colors"
                :class="
                    s.value === segment
                        ? 'bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-300'
                        : 'text-muted hover:text-highlighted'
                "
                @click="segment = s.value"
            >
                {{ s.label }}
                <span v-if="s.count !== undefined" class="opacity-60">{{ s.count }}</span>
            </button>
        </div>
        <slot />
    </div>
</template>
