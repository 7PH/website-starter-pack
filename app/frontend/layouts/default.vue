<script lang="ts" setup>
import PageHeader from '~/components/PageHeader.vue';
import ModalConfirm from '~/components/modal/ModalConfirm.vue';
</script>

<template>
    <div>
        <PageHeader />
        <NuxtPage />

        <!-- Global modals -->
        <ModalConfirm />

        <!-- PrimeVue Toast -->
        <Toast position="top-center" />
    </div>
</template>
