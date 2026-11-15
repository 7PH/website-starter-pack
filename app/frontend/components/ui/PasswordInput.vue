<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->

<script lang="ts" setup>
/** Password input with a labelled show/hide toggle. Other attributes (autocomplete, placeholder...) reach the UInput. */
defineProps<{ error?: boolean }>();

const model = defineModel<string>({ required: true });
const { t } = useI18n();
const visible = ref(false);
</script>

<template>
    <UInput
        v-model="model"
        :type="visible ? 'text' : 'password'"
        :color="error ? 'error' : undefined"
        :ui="{ trailing: 'pe-1' }"
        class="w-full"
    >
        <template #trailing>
            <UButton
                color="neutral"
                variant="link"
                size="sm"
                :icon="visible ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                :aria-label="visible ? t('core.auth.hidePassword') : t('core.auth.showPassword')"
                :aria-pressed="visible"
                @click="visible = !visible"
            />
        </template>
    </UInput>
</template>
