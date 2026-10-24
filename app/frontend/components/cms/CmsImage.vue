<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Responsive <img> for a library photo. Crops (object-fit: cover from the caller's class) keep the focal point in frame. */
const props = withDefaults(
    defineProps<{
        media: CmsMediaRead;
        sizes?: string;
        alt?: string;
        eager?: boolean;
    }>(),
    { sizes: '100vw', alt: undefined },
);

const srcset = computed(() =>
    Object.entries(props.media.urls)
        .map(([width, url]) => `${url} ${width}w`)
        .join(', '),
);
const objectPosition = computed(() => `${props.media.focal_x * 100}% ${props.media.focal_y * 100}%`);
</script>

<template>
    <img
        :src="media.src"
        :srcset="srcset"
        :sizes="sizes"
        :width="media.width"
        :height="media.height"
        :alt="alt ?? media.alt"
        :loading="eager ? 'eager' : 'lazy'"
        decoding="async"
        :style="{ objectPosition }"
    />
</template>
