<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
withDefaults(
    defineProps<{
        gradient?: boolean;
    }>(),
    {
        gradient: true,
    },
);
</script>

<template>
    <div class="page-wrapper" :class="{ 'with-gradient': gradient }">
        <slot />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.page-wrapper {
    @apply min-h-dvh flex flex-col;
    @apply bg-gray-50 dark:bg-slate-900;
}

.page-wrapper.with-gradient {
    @apply bg-gradient-to-br from-gray-50 via-gray-100 to-gray-50;
    @apply dark:from-slate-900 dark:via-slate-800 dark:to-slate-900;
    background-attachment: fixed;
}
</style>
