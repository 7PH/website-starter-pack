<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import ImpersonationBanner from '~/components/admin/ImpersonationBanner.vue';
import PageHeader from '~/components/PageHeader.vue';
import ModalConfirm from '~/components/modal/ModalConfirm.vue';
import ModalAuth from '~/components/modal/ModalAuth.vue';
</script>

<template>
    <UApp>
        <ImpersonationBanner />
        <PageHeader />
        <NuxtPage />

        <!-- Global modals -->
        <ModalConfirm />
        <ModalAuth />
    </UApp>
</template>
