<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    layout: 'admin',
    middleware: ['admin'],
});

const { t } = useI18n();
</script>

<template>
    <OrganizationsDetail
        :is-admin-view="true"
        back-link="/admin/organizations"
        :back-link-text="t('core.organizations.backToList')"
    />
</template>
