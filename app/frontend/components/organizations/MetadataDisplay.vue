<!--
Project-specific organization custom data display fields.
Add your custom read-only display here. They will be shown in the organization info card.

Example:
    <div v-if="customData.rne" class="flex flex-col gap-1">
        <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">RNE Code</span>
        <span class="text-sm text-gray-900 dark:text-gray-100">{{ customData.rne }}</span>
    </div>
-->

<script lang="ts" setup>
defineProps<{
    customData: OrganizationCustomData;
}>();
</script>

<template>
    <div>
        <!-- Add your custom display fields here -->
    </div>
</template>
