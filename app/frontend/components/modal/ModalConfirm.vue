<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
import type { ConfirmModalOptions } from '~/types/modal';

const MODAL_NAME = 'confirm';

const modal = useModal();

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
const confirmColor = computed(() => options.value.confirmColor ?? 'primary');

// Actions
function confirm() {
    modal.close(MODAL_NAME, true);
}

function cancel() {
    modal.close(MODAL_NAME, false);
}
</script>

<template>
    <UModal v-model:open="isOpen" :title="title" @close="cancel">
        <template #body>
            <p class="text-gray-600 dark:text-gray-400">
                {{ message }}
            </p>
        </template>

        <template #footer>
            <div class="flex justify-end gap-3">
                <UButton
                    variant="outline"
                    color="neutral"
                    @click="cancel"
                >
                    {{ cancelText }}
                </UButton>
                <UButton
                    :color="confirmColor"
                    @click="confirm"
                >
                    {{ confirmText }}
                </UButton>
            </div>
        </template>
    </UModal>
</template>
