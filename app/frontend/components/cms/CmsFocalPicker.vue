<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Click (or arrow keys) on the photo to set the point kept in frame when it gets cropped. */
defineProps<{ media: CmsMediaRead }>();
const { t } = useI18n();
const x = defineModel<number>('x', { required: true });
const y = defineModel<number>('y', { required: true });

const clamp = (v: number) => Math.round(Math.min(1, Math.max(0, v)) * 1000) / 1000;

function onClick(event: MouseEvent) {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    x.value = clamp((event.clientX - rect.left) / rect.width);
    y.value = clamp((event.clientY - rect.top) / rect.height);
}

const STEP = 0.05;
const KEYS: Record<string, [number, number]> = {
    ArrowLeft: [-STEP, 0],
    ArrowRight: [STEP, 0],
    ArrowUp: [0, -STEP],
    ArrowDown: [0, STEP],
};

function onKey(event: KeyboardEvent) {
    const delta = KEYS[event.key];
    if (!delta) return;
    event.preventDefault();
    x.value = clamp(x.value + delta[0]);
    y.value = clamp(y.value + delta[1]);
}
</script>

<template>
    <!-- Natural aspect ratio (no letterboxing), so click coordinates map straight to 0..1. -->
    <div
        class="relative cursor-crosshair select-none rounded-lg overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
        tabindex="0"
        role="group"
        :aria-label="t('cms.media.focal')"
        :aria-valuetext="`${Math.round(x * 100)}%, ${Math.round(y * 100)}%`"
        @click="onClick"
        @keydown="onKey"
    >
        <CmsImage :media="media" sizes="(min-width: 640px) 480px, 100vw" eager class="block w-full" draggable="false" />
        <span
            class="absolute size-8 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-primary-500/40 shadow-[0_0_0_2px_rgba(0,0,0,0.4)] pointer-events-none transition-all duration-150"
            :style="{ left: `${x * 100}%`, top: `${y * 100}%` }"
        />
    </div>
</template>
