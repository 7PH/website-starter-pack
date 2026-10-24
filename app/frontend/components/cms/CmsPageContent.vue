<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Default look of a free page: title, cover, body. Override 'CmsPageContent' to render your own templates.
const props = defineProps<{ page: CmsPageRead }>();

const body = computed(() => (typeof props.page.fields.body === 'string' ? props.page.fields.body : ''));
</script>

<template>
    <article class="max-w-3xl mx-auto px-4 py-12">
        <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-8">{{ page.title }}</h1>
        <CmsImage
            v-if="page.cover"
            :media="page.cover"
            sizes="(min-width: 768px) 768px, 100vw"
            class="w-full aspect-video object-cover rounded-xl mb-8"
            eager
        />
        <CmsRichText :html="body" />
    </article>
</template>
