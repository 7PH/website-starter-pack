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
            <!-- The footer scrolls with the page: pinned, it took a band of every screen. Still at the bottom on a short page. -->
            <main
                id="main-content"
                tabindex="-1"
                class="flex flex-1 min-h-0 flex-col overflow-y-auto overflow-x-hidden outline-none"
            >
                <div class="flex flex-1 flex-col">
                    <!-- error.vue fills the slot, routes get the page. -->
                    <slot><NuxtPage /></slot>
                </div>
                <component :is="PageFooter" v-if="showFooter" />
            </main>

            <!-- Global modals -->
            <ModalConfirm />
            <ModalAuth />
        </UApp>
    </UiPageWrapper>
</template>
