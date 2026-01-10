<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
/**
 * Card header component with title and optional actions slot.
 * Provides consistent layout for UCard headers.
 */
defineProps<{
    /** Title text to display */
    title?: string;
}>();
</script>

<template>
    <div class="flex justify-between items-center">
        <span class="font-semibold">
            <slot name="title">{{ title }}</slot>
        </span>
        <slot name="actions" />
    </div>
</template>
