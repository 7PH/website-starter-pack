<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
definePageMeta({
    middleware: ['auth'],
    auth: true,
});

const route = useRoute();
await navigateTo({ path: '/account', query: { ...route.query, tab: 'billing' } }, { replace: true });
</script>

<template>
    <div />
</template>
