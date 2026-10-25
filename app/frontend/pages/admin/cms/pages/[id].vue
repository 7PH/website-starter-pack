<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
definePageMeta({
    middleware: ['admin', 'cms'],
});

const route = useRoute();
const id = Number(route.params.id);
if (!Number.isInteger(id)) {
    throw createError({ statusCode: 404, statusMessage: 'Page not found', fatal: true });
}
</script>

<template>
    <CmsPageEditor :endpoint="`/cms/admin/pages/${id}`" />
</template>
