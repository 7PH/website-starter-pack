<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
withDefaults(
    defineProps<{
        as?: string;
    }>(),
    {
        as: 'div',
    },
);
</script>

<template>
    <component :is="as" class="hover-card">
        <slot />
    </component>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.hover-card {
    @apply rounded-lg bg-white dark:bg-slate-800;
    @apply border-2 border-gray-200 dark:border-slate-700;
    @apply transition-all;
}

.hover-card:hover {
    @apply border-primary-300 dark:border-primary-500;
    @apply shadow-lg -translate-y-1;
}
</style>
