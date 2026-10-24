<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Route component for free CMS pages. Lives outside pages/: nuxt.config.ts registers it only when CMS_ENABLED.
import CmsPageContentDefault from '~/components/cms/CmsPageContent.vue';
import { buildCanonicalUrl } from '~/composables/useCanonical';

const route = useRoute();
const segments = [route.params.slug ?? []].flat();
if (segments.length !== 1) {
    throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true });
}

const { data: page, error } = await useCmsPage(segments[0]!);
if (error.value) {
    throw createError({ ...error.value, fatal: true });
}
if (!page.value) {
    throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true });
}

const PageContent = useOverridable('CmsPageContent', CmsPageContentDefault);

useSeoMeta({
    title: () => page.value?.seo_title,
    description: () => page.value?.seo_description,
    ogTitle: () => page.value?.seo_title,
    ogDescription: () => page.value?.seo_description,
    ogImage: () => page.value?.cover?.src,
    ogType: 'article',
    ogUrl: buildCanonicalUrl(route.path, useRuntimeConfig().public.baseUrl),
    twitterCard: () => (page.value?.cover ? 'summary_large_image' : 'summary'),
});
useCanonical();
</script>

<template>
    <div v-if="page">
        <component :is="PageContent" :page="page" />
        <CmsPageEditButton :page="page" />
    </div>
</template>
