<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import type { ConfirmModalOptions } from '~/types/modal';

const MODAL_NAME = 'confirm';

const modal = useModalStore();

// Register on mount
onMounted(() => {
    modal.register(MODAL_NAME);
});

onUnmounted(() => {
    modal.unregister(MODAL_NAME);
});

// Get modal state
const isOpen = computed(() => modal.isOpen(MODAL_NAME));
const options = computed(() => modal.getOptions(MODAL_NAME) as ConfirmModalOptions);

// Default values
const title = computed(() => options.value.title ?? 'Confirm');
const message = computed(() => options.value.message ?? 'Are you sure you want to continue?');
const confirmText = computed(() => options.value.confirmText ?? 'Confirm');
const cancelText = computed(() => options.value.cancelText ?? 'Cancel');
const confirmSeverity = computed(() => {
    const color = options.value.confirmColor ?? 'primary';
    // Map Nuxt UI colors to PrimeVue severities
    if (color === 'error') return 'danger';
    if (color === 'warning') return 'warn';
    return 'primary';
});

// Actions
function confirm() {
    modal.close(MODAL_NAME, true);
}

function cancel() {
    modal.close(MODAL_NAME, false);
}
</script>

<template>
    <Dialog
        v-model:visible="isOpen"
        :header="title"
        modal
        :closable="true"
        :draggable="false"
        class="w-full max-w-md"
        @hide="cancel"
    >
        <p class="text-gray-600 dark:text-gray-400">
            {{ message }}
        </p>

        <template #footer>
            <div class="flex justify-end gap-3">
                <Button :label="cancelText" text severity="secondary" @click="cancel" />
                <Button :label="confirmText" :severity="confirmSeverity" @click="confirm" />
            </div>
        </template>
    </Dialog>
</template>
