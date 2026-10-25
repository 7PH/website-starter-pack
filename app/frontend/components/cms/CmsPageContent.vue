<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
// Default look of a free page: title, cover, body, each with a quick-edit pencil for editors. Override 'CmsPageContent' to render your own templates.
const props = defineProps<{ page: CmsPageRead }>();

const { t } = useI18n();

const body = computed(() => (typeof props.page.fields.body === 'string' ? props.page.fields.body : ''));
</script>

<template>
    <article class="max-w-3xl mx-auto px-4 py-12">
        <CmsEditable :page="page" field="title" class="mb-8">
            <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100">{{ page.title }}</h1>
        </CmsEditable>
        <CmsEditable v-if="page.cover" :page="page" field="cover">
            <CmsImage
                :media="page.cover"
                sizes="(min-width: 768px) 768px, 100vw"
                class="mb-8 w-full aspect-video object-cover rounded-xl"
                eager
            />
        </CmsEditable>
        <CmsEditable v-else :page="page" field="cover" :add-label="t('cms.inline.addCover')" class="mb-8" />
        <CmsEditable :page="page" field="body">
            <CmsRichText :html="body" />
        </CmsEditable>
    </article>
</template>
