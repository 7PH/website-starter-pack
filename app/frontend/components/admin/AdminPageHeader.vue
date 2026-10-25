<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Top of an admin page: title with an optional count pill, description, actions on the right.
defineProps<{
    title: string;
    /** Shown as a pill after the title (eg the number of rows) */
    count?: number | string;
    description?: string;
}>();
</script>

<template>
    <div class="flex flex-wrap items-end justify-between gap-4">
        <div class="flex min-w-0 flex-col gap-1">
            <div class="flex flex-wrap items-center gap-2.5">
                <h1 class="text-[22px] font-extrabold tracking-[-0.01em] text-highlighted md:text-[28px]">
                    {{ title }}
                </h1>
                <span
                    v-if="count !== undefined"
                    class="rounded-full bg-elevated px-2 py-0.5 text-xs font-extrabold text-toned"
                >
                    {{ count }}
                </span>
                <!-- Extra pills next to the title (eg a "Read-only" UBadge) -->
                <slot name="badges" />
            </div>
            <p v-if="description || $slots.description" class="text-sm text-muted">
                <slot name="description">{{ description }}</slot>
            </p>
        </div>
        <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
            <slot name="actions" />
        </div>
    </div>
</template>
