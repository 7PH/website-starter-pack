<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
defineProps<{
    compact?: boolean;
}>();
</script>

<template>
    <UiPageTitleBanner :compact="compact">
        <span class="title-row">
            <span>Admin</span>
            <UBadge label="Admin" color="error" size="sm" icon="i-lucide-shield" />
        </span>
        <template #subtitle>Manage users, organizations, and system settings</template>
        <template #subnav>
            <AdminSubnav />
        </template>
    </UiPageTitleBanner>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.title-row {
    @apply inline-flex items-center gap-3;
}
</style>
