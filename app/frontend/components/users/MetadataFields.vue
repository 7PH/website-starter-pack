<!--
Project-specific user custom data form fields.

Appears in:
  - /account profile form (user editing themselves)
  - /admin/users/[id] edit form (admin editing any user)

What to render: inputs for whichever UserCustomData fields you want
editable. Values are two-way bound through `update('<field>', value)`.
Leave this <div /> empty if your app doesn't need custom fields.

The generated TS interface `UserCustomData` (from schemas/user_ext.py) drives
auto-completion on `customData.<field>` and on `update('<field>', ...)`.

Example:
    <UFormField label="User type">
        <USelect
            :model-value="customData.user_type ?? 'STUDENT'"
            :items="['STUDENT', 'TEACHER']"
            class="w-full"
            @update:model-value="update('user_type', $event)"
        />
    </UFormField>

    <UFormField label="Phone">
        <UInput
            :model-value="customData.phone ?? ''"
            placeholder="Optional"
            class="w-full"
            @update:model-value="update('phone', $event || null)"
        />
    </UFormField>
-->

<script lang="ts" setup>
const props = defineProps<{
    customData: UserCustomData;
}>();

const emit = defineEmits<{
    'update:customData': [value: UserCustomData];
}>();

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function update<K extends keyof UserCustomData>(key: K, value: UserCustomData[K]) {
    emit('update:customData', { ...props.customData, [key]: value });
}
</script>

<template>
    <div />
</template>
