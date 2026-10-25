<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Bordered admin card. Rows go in the default slot, separated by a border; give each row its own padding (px-4.5 py-3).
defineProps<{
    title?: string;
    /** Faint text on the right of the title (eg "3 keys") */
    meta?: string;
}>();
</script>

<template>
    <section class="overflow-hidden rounded-xl border border-default bg-default">
        <header
            v-if="title || $slots.title"
            class="flex items-center justify-between gap-3 border-b border-default px-4.5 py-3"
        >
            <h2 class="text-[15px] font-extrabold text-highlighted">
                <slot name="title">{{ title }}</slot>
            </h2>
            <slot name="meta">
                <span v-if="meta" class="text-[13px] text-dimmed">{{ meta }}</span>
            </slot>
        </header>
        <!-- Column header row: lay it out with the same grid as the rows -->
        <div
            v-if="$slots.columns"
            class="border-b border-default px-4.5 py-2.5 text-xs font-extrabold tracking-[.05em] text-dimmed uppercase"
        >
            <slot name="columns" />
        </div>
        <div class="divide-y divide-default">
            <slot />
        </div>
    </section>
</template>
