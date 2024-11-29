<script setup lang="ts">
const config = useRuntimeConfig();
const api = useApi();

const data = import.meta.client && (await api.fetch("/hello-world"));
</script>

<template>
    <div>
        <p>BASE URL: {{ config.public.apiBase }}</p>
        <client-only>
            <p>DATA: {{ data }}</p>
        </client-only>
    </div>
</template>
