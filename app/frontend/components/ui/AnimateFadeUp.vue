<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
withDefaults(
    defineProps<{
        delay?: number;
        duration?: number;
        distance?: number;
    }>(),
    {
        delay: 0,
        duration: 600,
        distance: 20,
    },
);

const isVisible = ref(false);

onMounted(() => {
    requestAnimationFrame(() => {
        isVisible.value = true;
    });
});
</script>

<template>
    <div
        class="animate-fade-up"
        :class="{ 'is-visible': isVisible }"
        :style="{
            '--delay': `${delay}ms`,
            '--duration': `${duration}ms`,
            '--distance': `${distance}px`,
        }"
    >
        <slot />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.animate-fade-up {
    opacity: 0;
    transform: translateY(var(--distance));
    transition:
        opacity var(--duration) var(--ease-out-expo),
        transform var(--duration) var(--ease-out-expo);
    transition-delay: var(--delay);
}

.animate-fade-up.is-visible {
    opacity: 1;
    transform: translateY(0);
}
</style>
