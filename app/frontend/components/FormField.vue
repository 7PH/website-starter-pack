<script lang="ts" setup>
defineProps<{
    label?: string;
    error?: string;
}>();
</script>

<template>
    <div class="flex flex-col gap-1">
        <label v-if="label" class="text-sm font-medium text-gray-700 dark:text-gray-300">
            {{ label }}
        </label>
        <slot />
        <small v-if="error" class="text-red-500 text-sm">{{ error }}</small>
    </div>
</template>
