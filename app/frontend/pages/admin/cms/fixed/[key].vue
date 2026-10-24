<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
definePageMeta({
    middleware: ['admin', 'cms'],
});

const route = useRoute();
</script>

<template>
    <div class="page-box">
        <AdminPageBanner />
        <CmsPageEditor :endpoint="`/cms/admin/fixed/${encodeURIComponent(String(route.params.key))}`" />
    </div>
</template>
