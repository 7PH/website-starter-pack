<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
defineProps<{
    compact?: boolean;
}>();
</script>

<template>
    <div class="page-title-banner" :class="{ compact, 'has-subnav': $slots.subnav }">
        <div class="banner-content page-content-width">
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
    </div>
    <!-- Subnav is always sticky -->
    <div v-if="$slots.subnav" class="banner-subnav-sticky">
        <div class="banner-subnav-sticky-content page-content-width">
            <slot name="subnav" />
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.page-title-banner {
    @apply flex flex-col justify-between min-h-[140px] mb-6;

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

/* When subnav follows, reduce height and remove bottom border/margin (subnav will have them) */
.page-title-banner.has-subnav {
    @apply mb-0 min-h-0;
    border-bottom: none;
    padding-bottom: 0;
}

.page-title-banner.compact {
    @apply min-h-[100px];
    padding-top: 1rem;
    padding-bottom: 0.75rem;
}

.page-title-banner.compact.has-subnav {
    padding-bottom: 0;
}

.banner-content {
    @apply flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4;
}

.banner-left {
    @apply flex-1;
}

.banner-right {
    @apply flex items-center gap-2 lg:text-right;
}

/* Sticky subnav (sibling element at page level) */
.banner-subnav-sticky {
    @apply sticky z-30 mb-6 backdrop-blur-xl;

    top: 0;

    /* Full-bleed effect */
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    padding-left: calc(50vw - 50%);
    padding-right: calc(50vw - 50%);
    padding-top: 0.75rem;
    padding-bottom: 0.5rem;

    /* Same gradient as banner - appears seamless */
    background: var(--gradient-banner);
    border-bottom: 1px solid var(--border-brand);
}

/* Content inherits page-content-width from template class */
</style>
