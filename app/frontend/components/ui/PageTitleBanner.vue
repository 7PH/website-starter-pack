<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
defineProps<{
    compact?: boolean;
}>();
</script>

<template>
    <div class="page-title-banner" :class="{ compact }">
        <div class="banner-content">
            <div class="banner-left">
                <h4 class="font-semibold text-2xl mb-3 text-slate-800 dark:text-slate-100">
                    <slot />
                </h4>
                <div class="text-slate-600 dark:text-slate-400">
                    <slot name="subtitle" />
                </div>
            </div>
            <div v-if="$slots.actions" class="banner-right">
                <slot name="actions" />
            </div>
        </div>
        <div v-if="$slots.subnav" class="banner-subnav">
            <slot name="subnav" />
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.page-title-banner {
    @apply flex flex-col justify-between min-h-[200px] mb-6;

    /* Full-bleed effect */
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    padding-left: calc(50vw - 50%);
    padding-right: calc(50vw - 50%);
    padding-top: 2rem;
    padding-bottom: 1.5rem;

    /* Vibrant multi-color gradient (uses theme colors) */
    background: var(--gradient-banner);

    /* Soft bottom edge (uses theme brand color) */
    border-bottom: 1px solid var(--border-brand);
}

/* Dark mode */
:global(.dark) .page-title-banner {
    background: var(--gradient-banner-dark);
    border-bottom: 1px solid var(--border-brand-dark);
}

.page-title-banner.compact {
    @apply min-h-[140px];
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}

.banner-content {
    @apply flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4;
    @apply w-full mx-auto;
    max-width: var(--page-max-width);
}

.banner-left {
    @apply flex-1;
}

.banner-right {
    @apply flex items-center gap-2 lg:text-right;
}

.banner-subnav {
    @apply w-full mx-auto;
    max-width: var(--page-max-width);
}
</style>
