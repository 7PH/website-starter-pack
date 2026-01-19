<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
definePageMeta({
    middleware: ['auth'],
});

const { t } = useI18n();
</script>

<template>
    <div class="page-box">
        <UiPageTitleBanner compact>
            {{ t('core.organizations.title') }}
            <template #subtitle>
                {{ t('core.organizations.description') }}
            </template>
        </UiPageTitleBanner>

        <OrganizationsDetail
            :is-admin-view="false"
            back-link="/organizations"
            :back-link-text="t('core.organizations.backToList')"
        />
    </div>
</template>
