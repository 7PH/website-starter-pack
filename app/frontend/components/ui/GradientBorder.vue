<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
withDefaults(
    defineProps<{
        position?: 'top' | 'bottom' | 'left' | 'right';
    }>(),
    {
        position: 'bottom',
    },
);
</script>

<template>
    <div class="gradient-border" :class="`position-${position}`" />
</template>

<style scoped>
@reference "~/assets/css/main.css";

.gradient-border {
    @apply absolute pointer-events-none;
}

.position-top {
    @apply top-0 left-0 right-0 h-px;
}
.position-bottom {
    @apply bottom-0 left-0 right-0 h-px;
}
.position-left {
    @apply top-0 bottom-0 left-0 w-px;
}
.position-right {
    @apply top-0 bottom-0 right-0 w-px;
}

/* Horizontal gradients - uses theme primary color */
.position-top,
.position-bottom {
    @apply bg-gradient-to-r from-transparent via-primary-400/50 to-transparent;
    @apply dark:via-primary-500/30;
}

/* Vertical gradients */
.position-left,
.position-right {
    @apply bg-gradient-to-b from-transparent via-primary-400/50 to-transparent;
    @apply dark:via-primary-500/30;
}
</style>
