<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
/** First thing a keyboard reaches: jumps past the header to the page. The target is the layout's <main id="main-content">. */
const { t } = useI18n();
</script>

<template>
    <a
        href="#main-content"
        class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-default focus:px-4 focus:py-2 focus:shadow-lg focus:ring-2 focus:ring-primary"
    >
        {{ t('core.common.skipToContent') }}
    </a>
</template>
