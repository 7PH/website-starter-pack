<script lang="ts" setup>
import type { NuxtError } from '#app';

const props = defineProps<{ error: NuxtError }>();
const { t } = useI18n();

const notFound = computed(() => props.error.statusCode === 404);
const title = computed(() => t(notFound.value ? 'core.errorPage.notFoundTitle' : 'core.errorPage.title'));

useSeoMeta({ title, robots: 'noindex' });
</script>

<template>
    <!-- Default layout whatever the failed route asked for: other layouts have no slot for this content. -->
    <NuxtLayout name="default">
        <div class="page-content-width px-4 py-24 text-center">
            <p class="text-5xl font-bold text-primary-500">{{ error.statusCode }}</p>
            <h1 class="mt-4 text-2xl font-semibold">{{ title }}</h1>
            <p class="mt-2 text-gray-600 dark:text-gray-400">
                {{ t(notFound ? 'core.errorPage.notFoundMessage' : 'core.errorPage.message') }}
            </p>
            <!-- clearError, not a link: the error state would stay up. -->
            <UButton class="mt-8" :label="t('core.common.goToHome')" @click="clearError({ redirect: '/' })" />
        </div>
    </NuxtLayout>
</template>
