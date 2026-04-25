<script lang="ts" setup>
// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
//
// Renders a conversation message as markdown. All sanitization happens in
// utils/markdown.ts (the security boundary); this component is just a styled
// wrapper around v-html on the sanitized output.

import { renderMarkdown } from '~/utils/markdown';

const props = defineProps<{
    content: string;
}>();

const html = computed(() => renderMarkdown(props.content));
</script>

<template>
    <!-- eslint-disable-next-line vue/no-v-html -- html is sanitized by renderMarkdown (utils/markdown.ts) -->
    <div class="message-md" v-html="html" />
</template>

<style scoped>
@reference "~/assets/css/main.css";

.message-md {
    @apply text-gray-900 dark:text-gray-100 break-words;
}

.message-md :deep(p) {
    @apply my-1;
}

.message-md :deep(h1),
.message-md :deep(h2),
.message-md :deep(h3),
.message-md :deep(h4),
.message-md :deep(h5),
.message-md :deep(h6) {
    @apply mt-3 mb-1 font-semibold leading-tight;
}

.message-md :deep(h1) {
    @apply text-lg;
}

.message-md :deep(h2) {
    @apply text-base;
}

.message-md :deep(h3),
.message-md :deep(h4),
.message-md :deep(h5),
.message-md :deep(h6) {
    @apply text-sm;
}

.message-md :deep(p:first-child) {
    @apply mt-0;
}

.message-md :deep(p:last-child) {
    @apply mb-0;
}

.message-md :deep(ul),
.message-md :deep(ol) {
    @apply my-1 pl-5;
}

.message-md :deep(ul) {
    @apply list-disc;
}

.message-md :deep(ol) {
    @apply list-decimal;
}

.message-md :deep(li) {
    @apply my-0.5;
}

.message-md :deep(strong) {
    @apply font-semibold;
}

.message-md :deep(em) {
    @apply italic;
}

.message-md :deep(code) {
    @apply rounded px-1 py-0.5 text-sm font-mono bg-gray-200 dark:bg-gray-700;
}

.message-md :deep(pre) {
    @apply my-2 rounded p-2 overflow-x-auto bg-gray-200 dark:bg-gray-700;
}

.message-md :deep(pre code) {
    @apply p-0 bg-transparent text-sm;
}

.message-md :deep(blockquote) {
    @apply my-2 pl-3 border-l-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 italic;
}

.message-md :deep(a) {
    @apply text-primary-600 dark:text-primary-400 underline;
}

.message-md :deep(a:hover) {
    @apply text-primary-700 dark:text-primary-300;
}
</style>
