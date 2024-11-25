<script setup lang="ts">
const config = useRuntimeConfig();
const api = useApi();

const data = await api.fetch('/hello-world');
</script>

<template>
    <div>
        <p>BASE URL: {{ config.public.apiBase }}</p>
        <p>DATA: {{ data }}</p>
    </div>
</template>
