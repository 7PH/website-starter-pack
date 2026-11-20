<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
/** Loads the next page when scrolled into view. Still a button, for keyboards and when the observer can't tell. */
// `paused`: the last load failed, so wait for a click instead of retrying in a loop.
const props = defineProps<{ loading: boolean; paused?: boolean }>();
const emit = defineEmits<{ load: [] }>();
const { t } = useI18n();

const button = useTemplateRef<{ $el: HTMLElement }>('button');
const visible = ref(false);
useIntersectionObserver(
    () => button.value?.$el,
    ([entry]) => (visible.value = !!entry?.isIntersecting),
    { rootMargin: '400px' },
);
// Also after each page: a short page leaves the button in view without a new intersection event.
watch([visible, () => props.loading], () => {
    if (visible.value && !props.loading && !props.paused) emit('load');
});
</script>

<template>
    <UButton
        ref="button"
        :label="t('cms.media.loadMore')"
        :loading="loading"
        color="neutral"
        variant="outline"
        class="self-center"
        @click="emit('load')"
    />
</template>
