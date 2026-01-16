<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import ImpersonationBanner from '~/components/admin/ImpersonationBanner.vue';
import ModalAuth from '~/components/modal/ModalAuth.vue';
import ModalConfirm from '~/components/modal/ModalConfirm.vue';
import PageFooter from '~/components/PageFooter.vue';
import PageHeader from '~/components/PageHeader.vue';

const route = useRoute();
const showFooter = computed(() => !route.meta.hideFooter);
</script>

<template>
    <UiPageWrapper>
        <UApp class="flex flex-col flex-1 min-h-0">
            <ImpersonationBanner />
            <PageHeader />
            <main class="flex-1 min-h-0 flex flex-col overflow-y-auto overflow-x-hidden">
                <NuxtPage />
            </main>
            <PageFooter v-if="showFooter" />

            <!-- Global modals -->
            <ModalConfirm />
            <ModalAuth />
        </UApp>
    </UiPageWrapper>
</template>
