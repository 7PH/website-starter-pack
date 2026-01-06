<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
defineProps<{
    title: string;
    lastUpdated?: string;
}>();

const { t } = useI18n();
</script>

<template>
    <div class="legal-page">
        <div class="legal-container">
            <header class="legal-header">
                <h1 class="legal-title">{{ title }}</h1>
                <p v-if="lastUpdated" class="legal-updated">{{ t('core.legal.lastUpdated') }}: {{ lastUpdated }}</p>
            </header>

            <div class="legal-content">
                <slot />
            </div>

            <footer class="legal-footer">
                <NuxtLink to="/" class="back-link">
                    <UIcon name="i-lucide-arrow-left" />
                    {{ t('core.legal.backToHome') }}
                </NuxtLink>
            </footer>
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.legal-page {
    @apply min-h-screen py-12 px-4;
    @apply bg-gray-50 dark:bg-gray-900;
}

.legal-container {
    @apply max-w-3xl mx-auto;
}

.legal-header {
    @apply mb-8;
}

.legal-title {
    @apply text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2;
}

.legal-updated {
    @apply text-sm text-gray-500 dark:text-gray-400;
}

.legal-content {
    @apply bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8;
}

.legal-content :deep(h2) {
    @apply text-xl font-semibold text-gray-900 dark:text-gray-100 mt-8 mb-4;
}

.legal-content :deep(h2:first-child) {
    @apply mt-0;
}

.legal-content :deep(h3) {
    @apply text-lg font-medium text-gray-900 dark:text-gray-100 mt-6 mb-3;
}

.legal-content :deep(p) {
    @apply text-gray-600 dark:text-gray-300 mb-4 leading-relaxed;
}

.legal-content :deep(ul) {
    @apply list-disc list-inside text-gray-600 dark:text-gray-300 mb-4 space-y-2;
}

.legal-content :deep(a) {
    @apply text-primary-600 dark:text-primary-400 hover:underline;
}

.legal-content :deep(strong) {
    @apply font-semibold text-gray-700 dark:text-gray-200;
}

.legal-footer {
    @apply mt-8;
}

.back-link {
    @apply inline-flex items-center gap-2 text-gray-500 dark:text-gray-400;
    @apply hover:text-primary-600 dark:hover:text-primary-400 no-underline;
}
</style>
