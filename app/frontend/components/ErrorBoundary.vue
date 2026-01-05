<script setup lang="ts">
// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

interface Props {
    /** Error object or message to display */
    error?: Error | string | null;
    /** Custom title for the error display */
    title?: string;
    /** Whether to show retry button */
    showRetry?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    error: null,
    title: 'Something went wrong',
    showRetry: true,
});

const emit = defineEmits<{
    retry: [];
}>();

const errorMessage = computed(() => {
    if (!props.error) return '';
    if (typeof props.error === 'string') return props.error;
    return props.error.message || 'An unexpected error occurred';
});

function handleRetry() {
    emit('retry');
}
</script>

<template>
    <div v-if="error" class="flex flex-col items-center justify-center py-12 px-4 text-center">
        <div class="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
            <UIcon name="i-lucide-alert-triangle" class="w-8 h-8 text-red-500 dark:text-red-400" />
        </div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
            {{ title }}
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-4">
            {{ errorMessage }}
        </p>
        <div class="flex gap-2">
            <UButton v-if="showRetry" label="Try again" icon="i-lucide-refresh-cw" @click="handleRetry" />
            <slot name="actions" />
        </div>
    </div>
    <slot v-else />
</template>
