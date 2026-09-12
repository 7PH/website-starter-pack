<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
definePageMeta({
    middleware: ['auth'],
    auth: true,
});

const config = useRuntimeConfig();
const route = useRoute();

// Guard here rather than in route middleware: the navigateTo below wins the SSR response even
// after middleware has thrown.
if (String(config.public.stripeEnabled) !== 'true') {
    throw createError({ statusCode: 404, statusMessage: 'Not Found', fatal: true });
}

await navigateTo({ path: '/account', query: { ...route.query, tab: 'billing' } }, { replace: true });
</script>

<template>
    <div />
</template>
