<script setup lang="ts">
const config = useRuntimeConfig();
const api = useApi();

const data = import.meta.client && (await api.get("/healthcheck"));
</script>

<template>
    <div>
        <p>apiBase: {{ config.public.apiBase }}</p>
        <client-only>
            <p>DATA: {{ data }}</p>
        </client-only>
        <UButton>Button</UButton>
    </div>
</template>
