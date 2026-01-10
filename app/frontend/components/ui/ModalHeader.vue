<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
/**
 * Modal header component with title and close button.
 * Provides consistent layout for UModal content headers.
 */
defineProps<{
    /** Title text to display */
    title: string;
}>();

const emit = defineEmits<{
    close: [];
}>();
</script>

<template>
    <div class="flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ title }}</h3>
        <UButton icon="i-lucide-x" color="neutral" variant="ghost" size="xs" @click="emit('close')" />
    </div>
</template>
