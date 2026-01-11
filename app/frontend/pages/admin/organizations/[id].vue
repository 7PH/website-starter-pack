<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['admin'],
});

const { t } = useI18n();
</script>

<template>
    <div class="page-box">
        <UiPageTitleBanner>
            Admin
            <template #subtitle> Manage users, organizations, and system settings </template>
            <template #subnav>
                <AdminSubnav />
            </template>
        </UiPageTitleBanner>

        <OrganizationsDetail
            :is-admin-view="true"
            back-link="/admin/organizations"
            :back-link-text="t('core.organizations.backToList')"
        />
    </div>
</template>
