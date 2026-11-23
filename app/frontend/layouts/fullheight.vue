<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
import ImpersonationBanner from '~/components/admin/ImpersonationBanner.vue';
import ModalAuth from '~/components/modal/ModalAuth.vue';
import ModalConfirm from '~/components/modal/ModalConfirm.vue';
import PageFooterDefault from '~/components/PageFooter.vue';
import PageHeaderDefault from '~/components/PageHeader.vue';

const route = useRoute();
const showFooter = computed(() => !route.meta.hideFooter);

const PageHeader = useOverridable('PageHeader', PageHeaderDefault);
const PageFooter = useOverridable('PageFooter', PageFooterDefault);
const { uiLocale } = useAppLocale();
</script>

<template>
    <UiPageWrapper>
        <UApp :locale="uiLocale" class="flex flex-col flex-1 min-h-0">
            <UiSkipLink />
            <ImpersonationBanner />
            <component :is="PageHeader" />
            <main
                id="main-content"
                tabindex="-1"
                class="flex-1 min-h-0 flex flex-col overflow-y-auto overflow-x-hidden outline-none"
            >
                <NuxtPage />
            </main>
            <component :is="PageFooter" v-if="showFooter" />

            <!-- Global modals -->
            <ModalConfirm />
            <ModalAuth />
        </UApp>
    </UiPageWrapper>
</template>
