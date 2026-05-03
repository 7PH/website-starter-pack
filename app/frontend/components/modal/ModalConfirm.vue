<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import type { ConfirmModalOptions } from '~/types/modal';

const MODAL_NAME = 'confirm';

const { t } = useI18n();
const { isOpen, options, close } = useStoreModal<ConfirmModalOptions>(MODAL_NAME);

const title = computed(() => options.value.title ?? t('core.common.confirm'));
const message = computed(() => options.value.message ?? '');
const confirmText = computed(() => options.value.confirmText ?? t('core.common.confirm'));
const cancelText = computed(() => options.value.cancelText ?? t('core.common.cancel'));
const confirmColor = computed(() => options.value.confirmColor ?? 'primary');
const icon = computed(() => options.value.icon);
const tone = computed(() => options.value.tone ?? confirmColor.value);
</script>

<template>
    <UModal v-model:open="isOpen" :title="title" class="sm:max-w-md">
        <template #body>
            <div v-if="icon" class="modal-icon" :class="`modal-icon--${tone}`">
                <UIcon :name="icon" class="modal-icon__glyph" />
            </div>
            <p class="text-gray-600 dark:text-gray-400">
                {{ message }}
            </p>
        </template>

        <template #footer>
            <div class="flex justify-end gap-3">
                <UButton :label="cancelText" variant="ghost" color="neutral" @click="close(false)" />
                <UButton :label="confirmText" :color="confirmColor" @click="close(true)" />
            </div>
        </template>
    </UModal>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.modal-icon {
    @apply mb-3 inline-flex items-center justify-center size-10 rounded-full;
}
.modal-icon__glyph {
    @apply size-5;
}
.modal-icon--warning {
    @apply bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400;
}
.modal-icon--error {
    @apply bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400;
}
.modal-icon--success {
    @apply bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400;
}
.modal-icon--info {
    @apply bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400;
}
.modal-icon--primary {
    @apply bg-primary-100 text-primary-600 dark:bg-primary-900/40 dark:text-primary-400;
}
.modal-icon--neutral {
    @apply bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400;
}
</style>
