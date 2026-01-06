<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script setup lang="ts">
interface Props {
    title?: string;
    description?: string;
    icon?: string;
}

withDefaults(defineProps<Props>(), {
    title: 'No items found',
    description: '',
    icon: 'i-lucide-inbox',
});
</script>

<template>
    <div class="flex flex-col items-center justify-center py-12 px-4 text-center">
        <div class="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
            <UIcon :name="icon" class="w-8 h-8 text-gray-400 dark:text-gray-500" />
        </div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
            {{ title }}
        </h3>
        <p v-if="description" class="text-sm text-gray-500 dark:text-gray-400 max-w-sm">
            {{ description }}
        </p>
        <div v-if="$slots.action" class="mt-4">
            <slot name="action" />
        </div>
    </div>
</template>
