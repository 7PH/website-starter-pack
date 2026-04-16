<!--
Project-specific organization custom data form fields.
Add your custom form inputs here. They will be included in create/edit forms.

Example:
<UFormField label="RNE Code">
    <UInput :model-value="customData.rne" @update:model-value="update('rne', $event)" />
</UFormField>
-->

<script lang="ts" setup>
const props = defineProps<{
    customData: OrganizationCustomData;
}>();

const emit = defineEmits<{
    'update:customData': [value: OrganizationCustomData];
}>();

// Helper to update a single field while preserving others
function update<K extends keyof OrganizationCustomData>(key: K, value: OrganizationCustomData[K]) {
    emit('update:customData', { ...props.customData, [key]: value });
}
</script>

<template>
    <div />
</template>
