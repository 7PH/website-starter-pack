<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
defineProps<{
    compact?: boolean;
}>();

const { t } = useI18n();
const { isEditorOnly } = useCmsAccess();
</script>

<template>
    <UiPageTitleBanner :compact="compact">
        <span v-if="isEditorOnly">{{ t('cms.nav.editSite') }}</span>
        <span v-else class="title-row">
            <span>Admin</span>
            <UBadge label="Admin" color="error" size="sm" icon="i-lucide-shield" />
        </span>
        <template #subtitle>{{
            isEditorOnly ? t('cms.nav.subtitle') : 'Manage users, organizations, and system settings'
        }}</template>
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
