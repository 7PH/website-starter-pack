<!--
Project-specific organization custom data display fields.
Add your custom read-only display here. They will be shown in the organization info card.

Example:
<div v-if="customData.rne" class="info-item">
    <span class="info-label">RNE Code</span>
    <span class="info-value">{{ customData.rne }}</span>
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
