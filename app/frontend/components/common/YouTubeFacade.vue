<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/**
 * Lazy YouTube embed. Renders a thumbnail + play button by default and
 * only swaps in the real iframe on click, saving ~500KB of JS per
 * unplayed video. Uses `youtube-nocookie.com` so YouTube cookies are
 * not set until the user presses play.
 *
 * Privacy note: the default poster comes from `i.ytimg.com` (Google).
 * For zero contact with Google before play, pass a self-hosted `poster`.
 */

interface Props {
    videoId: string;
    /** Used as the button aria-label and the iframe title. */
    title: string;
    /** Start offset in seconds. */
    start?: number;
    /** Custom poster URL. Defaults to YouTube `maxresdefault.jpg` with `mqdefault.jpg` fallback. */
    poster?: string;
    /** CSS aspect-ratio for the player. */
    aspectRatio?: string;
}

const props = withDefaults(defineProps<Props>(), {
    start: undefined,
    poster: undefined,
    aspectRatio: '16/9',
});

const activated = ref(false);
const triedFallback = ref(false);
const posterFailed = ref(false);

const currentPosterUrl = computed(() => {
    if (props.poster) return props.poster;
    return triedFallback.value
        ? `https://i.ytimg.com/vi/${props.videoId}/mqdefault.jpg`
        : `https://i.ytimg.com/vi/${props.videoId}/maxresdefault.jpg`;
});

const iframeUrl = computed(() => {
    const params = new URLSearchParams({ autoplay: '1' });
    if (props.start) params.set('start', String(props.start));
    return `https://www.youtube-nocookie.com/embed/${props.videoId}?${params.toString()}`;
});

function onPosterError() {
    if (props.poster || triedFallback.value) {
        posterFailed.value = true;
        return;
    }
    triedFallback.value = true;
}
</script>

<template>
    <div :style="{ aspectRatio }" class="relative w-full overflow-hidden rounded-lg bg-gray-200 dark:bg-gray-800">
        <button
            v-if="!activated"
            type="button"
            :aria-label="title"
            class="group absolute inset-0 h-full w-full cursor-pointer border-0 bg-transparent p-0"
            @click="activated = true"
        >
            <img
                v-if="!posterFailed"
                :src="currentPosterUrl"
                alt=""
                width="1280"
                height="720"
                loading="lazy"
                class="absolute inset-0 h-full w-full object-cover"
                @error="onPosterError"
            />
            <span class="absolute inset-0 flex items-center justify-center">
                <svg
                    viewBox="0 0 68 48"
                    class="h-12 w-20 drop-shadow-md transition-transform group-hover:scale-110"
                    aria-hidden="true"
                >
                    <path
                        d="M66.52 7.74a8.28 8.28 0 0 0-5.83-5.86C55.65.5 34 .5 34 .5s-21.65 0-26.69 1.38a8.28 8.28 0 0 0-5.83 5.86A87.05 87.05 0 0 0 .5 24a87.05 87.05 0 0 0 1 16.26 8.28 8.28 0 0 0 5.82 5.86C12.35 47.5 34 47.5 34 47.5s21.65 0 26.69-1.38a8.28 8.28 0 0 0 5.83-5.86A87.05 87.05 0 0 0 67.5 24a87.05 87.05 0 0 0-1-16.26z"
                        fill="#f00"
                    />
                    <path d="M27 34l18-10-18-10z" fill="#fff" />
                </svg>
            </span>
        </button>
        <iframe
            v-else
            :src="iframeUrl"
            :title="title"
            allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowfullscreen
            loading="lazy"
            class="absolute inset-0 h-full w-full"
            style="border: 0"
        />
    </div>
</template>
