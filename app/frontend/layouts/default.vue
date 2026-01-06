<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import ImpersonationBanner from '~/components/admin/ImpersonationBanner.vue';
import PageHeader from '~/components/PageHeader.vue';
import PageFooter from '~/components/PageFooter.vue';
import ModalConfirm from '~/components/modal/ModalConfirm.vue';
import ModalAuth from '~/components/modal/ModalAuth.vue';
</script>

<template>
    <UApp class="min-h-dvh flex flex-col">
        <ImpersonationBanner />
        <PageHeader />
        <main class="flex-1 flex flex-col">
            <NuxtPage />
        </main>
        <PageFooter />

        <!-- Global modals -->
        <ModalConfirm />
        <ModalAuth />
    </UApp>
</template>
