<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
const props = defineProps<{
    open: boolean;
    isSending: boolean;
}>();

const emit = defineEmits<{
    'update:open': [value: boolean];
    invite: [email: string, isAdmin: boolean];
}>();

const { t } = useI18n();

const email = ref('');
const asOwner = ref(false);

watch(
    () => props.open,
    (v) => {
        if (v) {
            email.value = '';
            asOwner.value = false;
        }
    },
);

function submit() {
    if (!email.value) return;
    emit('invite', email.value, asOwner.value);
}
</script>

<template>
    <UModal :open="open" @update:open="emit('update:open', $event)">
        <template #content>
            <UCard>
                <template #header>
                    <UiModalHeader :title="t('core.organizations.addMember')" @close="emit('update:open', false)" />
                </template>

                <form class="form" @submit.prevent="submit">
                    <UFormField :label="t('core.organizations.email')" required>
                        <UInput v-model="email" type="email" :placeholder="t('core.organizations.emailPlaceholder')" />
                    </UFormField>
                    <div class="role-field">
                        <UCheckbox v-model="asOwner" :label="t('core.organizations.addAsAdmin')" />
                        <p class="role-hint">{{ t('core.organizations.roleTooltip') }}</p>
                    </div>
                    <UiFormActions>
                        <UButton
                            :label="t('core.organizations.cancel')"
                            color="neutral"
                            variant="outline"
                            @click="emit('update:open', false)"
                        />
                        <UButton
                            type="submit"
                            :label="t('core.organizations.add')"
                            :loading="isSending"
                            :disabled="!email"
                        />
                    </UiFormActions>
                </form>
            </UCard>
        </template>
    </UModal>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.form {
    @apply flex flex-col gap-4;
}

.role-field {
    @apply flex flex-col gap-1;
}

.role-hint {
    @apply text-xs text-gray-500 dark:text-gray-400 m-0 ml-6;
}
</style>
