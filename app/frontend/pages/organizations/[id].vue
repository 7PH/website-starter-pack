<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['auth'],
});

const { t } = useI18n();
</script>

<template>
    <div class="org-manage-page">
        <OrganizationsDetail
            :is-admin-view="false"
            back-link="/account?tab=organizations"
            :back-link-text="t('core.organizations.backToAccount')"
        />
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";
.org-manage-page {
    @apply max-w-4xl mx-auto px-4 py-8;
}
</style>
