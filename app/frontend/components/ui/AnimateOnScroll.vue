<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
const props = withDefaults(
    defineProps<{
        animation?: 'fade-up' | 'fade-in' | 'scale-in';
        delay?: number;
        duration?: number;
        threshold?: number;
        once?: boolean;
    }>(),
    {
        animation: 'fade-up',
        delay: 0,
        duration: 600,
        threshold: 0.1,
        once: true,
    },
);

const el = ref<HTMLElement>();
const isVisible = ref(false);

onMounted(() => {
    if (!el.value) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    isVisible.value = true;
                    if (props.once) {
                        observer.disconnect();
                    }
                } else if (!props.once) {
                    isVisible.value = false;
                }
            });
        },
        { threshold: props.threshold },
    );

    observer.observe(el.value);

    onUnmounted(() => observer.disconnect());
});
</script>

<template>
    <div
        ref="el"
        class="animate-on-scroll"
        :class="[animation, { 'is-visible': isVisible }]"
        :style="{
            '--delay': `${delay}ms`,
            '--duration': `${duration}ms`,
        }"
    >
        <slot />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.animate-on-scroll {
    transition-delay: var(--delay);
    transition-duration: var(--duration);
    transition-timing-function: var(--ease-out-expo);
}

/* Fade Up */
.animate-on-scroll.fade-up {
    opacity: 0;
    transform: translateY(20px);
    transition-property: opacity, transform;
}
.animate-on-scroll.fade-up.is-visible {
    opacity: 1;
    transform: translateY(0);
}

/* Fade In */
.animate-on-scroll.fade-in {
    opacity: 0;
    transition-property: opacity;
}
.animate-on-scroll.fade-in.is-visible {
    opacity: 1;
}

/* Scale In */
.animate-on-scroll.scale-in {
    opacity: 0;
    transform: scale(0.95);
    transition-property: opacity, transform;
}
.animate-on-scroll.scale-in.is-visible {
    opacity: 1;
    transform: scale(1);
}
</style>
