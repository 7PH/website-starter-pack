<!--
Project-specific user custom data form fields, shown on the SIGNUP form
(/login?mode=signup and the auth modal).

Purpose: collect UserCustomData values at account creation. Anything rendered
here is carried through `accountActions.signup(..., customData)` and arrives
on the backend as part of UserCreate.custom_data.

IMPORTANT: required-ness here is UI-only.
  - OAuth2 signups DO NOT go through this form — users get the defaults
    declared on UserCustomData (schemas/user_ext.py).
  - Direct POSTs to /users DO NOT go through this form either.
  If you need airtight "must have this field at creation" enforcement across
  every code path, add a Pydantic-level requirement yourself and handle the
  OAuth consequences.

How enforcement works:
  - Render inputs, two-way bound via `update('<field>', value)`.
  - Implement `validate()` to push error messages into the `errors` object
    and emit them. The parent form merges those errors into its own error
    bag and blocks submission if any are present.
  - `defineExpose({ validate })` lets the parent call it via ref.

Example (require user_type at signup):
    <script setup lang="ts">
    const props = defineProps<{ customData: UserCustomData }>();
    const emit = defineEmits<{
        'update:customData': [value: UserCustomData];
        validate: [errors: Record<string, string>];
    }>();
    function update<K extends keyof UserCustomData>(key: K, value: UserCustomData[K]) {
        emit('update:customData', { ...props.customData, [key]: value });
    }
    const error = ref<string | undefined>(undefined);
    function validate(): boolean {
        const errors: Record<string, string> = {};
        if (!props.customData.user_type) errors.user_type = 'Please pick a user type';
        error.value = errors.user_type;
        emit('validate', errors);
        return Object.keys(errors).length === 0;
    }
    defineExpose({ validate });
    const options = ['STUDENT', 'TEACHER'] as const;
    </script>

    <template>
        <UFormField label="I am a..." :error="error">
            <USelect
                :model-value="customData.user_type"
                :items="[...options]"
                placeholder="Select a type"
                class="w-full"
                @update:model-value="update('user_type', $event)"
            />
        </UFormField>
    </template>
-->

<script lang="ts" setup>
const props = defineProps<{
    customData: UserCustomData;
}>();

const emit = defineEmits<{
    'update:customData': [value: UserCustomData];
    // Emit validation errors keyed by field name. The parent merges them into
    // its form-level `errors` object so messages render next to standard
    // signup fields.
    validate: [errors: Record<string, string>];
}>();

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function update<K extends keyof UserCustomData>(key: K, value: UserCustomData[K]) {
    emit('update:customData', { ...props.customData, [key]: value });
}

// Exposed: parent calls `signupMetadataRef.value?.validate()` before submit.
// Returns true when there are no errors.
function validate(): boolean {
    const errors: Record<string, string> = {};
    // Populate errors here when you add required fields.
    emit('validate', errors);
    return Object.keys(errors).length === 0;
}

defineExpose({ validate });
</script>

<template>
    <div />
</template>
