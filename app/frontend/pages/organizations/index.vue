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
                {{ t('core.organizations.whatIsAnOrg') }}
            </template>
        </UiPageTitleBanner>

        <div class="organizations-content">
            <OrganizationsList />
        </div>
    </div>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.organizations-content {
    @apply max-w-5xl mx-auto;
}
</style>
