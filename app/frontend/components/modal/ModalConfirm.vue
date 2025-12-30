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

// Modal state - use safe accessors (handle SSR and initialization)
const isOpen = computed({
    get: () => {
        if (import.meta.server) return false;
        return modal.isOpen?.(MODAL_NAME) ?? false;
    },
    set: (value: boolean) => {
        if (!value) cancel();
    },
});

const options = computed((): ConfirmModalOptions => {
    if (import.meta.server) return {} as ConfirmModalOptions;
    return (modal.getOptions?.(MODAL_NAME) ?? {}) as ConfirmModalOptions;
});

// Default values
const title = computed(() => options.value.title ?? 'Confirm');
const message = computed(() => options.value.message ?? 'Are you sure you want to continue?');
const confirmText = computed(() => options.value.confirmText ?? 'Confirm');
const cancelText = computed(() => options.value.cancelText ?? 'Cancel');
const confirmColor = computed(() => {
    const color = options.value.confirmColor ?? 'primary';
    // Nuxt UI uses 'error' directly
    return color;
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
    <UModal v-model:open="isOpen" :title="title" class="sm:max-w-md">
        <template #body>
            <p class="text-gray-600 dark:text-gray-400">
                {{ message }}
            </p>
        </template>

        <template #footer>
            <div class="flex justify-end gap-3">
                <UButton :label="cancelText" variant="ghost" color="neutral" @click="cancel" />
                <UButton :label="confirmText" :color="confirmColor" @click="confirm" />
            </div>
        </template>
    </UModal>
</template>
