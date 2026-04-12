<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
const props = defineProps<{
    open: boolean;
    isCreating: boolean;
}>();

const emit = defineEmits<{
    'update:open': [value: boolean];
    create: [data: { name: string; email: string; description: string; custom_data: OrganizationCustomData }];
    close: [];
}>();

const { t } = useI18n();

const form = ref({
    name: '',
    email: '',
    description: '',
    custom_data: {} as OrganizationCustomData,
});

const isOpen = computed({
    get: () => props.open,
    set: (value) => emit('update:open', value),
});

function handleClose() {
    isOpen.value = false;
    emit('close');
}

function handleSubmit() {
    emit('create', { ...form.value });
}

function resetForm() {
    form.value = { name: '', email: '', description: '', custom_data: {} as OrganizationCustomData };
}

// Reset form when modal closes
watch(isOpen, (newValue) => {
    if (!newValue) {
        resetForm();
    }
});

defineExpose({ resetForm });
</script>

<template>
    <UModal v-model:open="isOpen">
        <template #content>
            <UCard>
                <template #header>
                    <UiModalHeader :title="t('core.organizations.createTitle')" @close="handleClose" />
                </template>

                <form class="create-form" @submit.prevent="handleSubmit">
                    <UFormField :label="t('core.organizations.name')" required>
                        <UInput
                            v-model="form.name"
                            :placeholder="t('core.organizations.orgNamePlaceholder')"
                            class="w-full"
                        />
                    </UFormField>
                    <UFormField :label="t('core.organizations.email')" required>
                        <UInput v-model="form.email" type="email" placeholder="contact@example.com" class="w-full" />
                    </UFormField>
                    <UFormField :label="t('core.organizations.descriptionLabel')">
                        <UTextarea
                            v-model="form.description"
                            :placeholder="t('core.organizations.optionalDescription')"
                            :rows="3"
                            class="w-full"
                        />
                    </UFormField>
                    <OrganizationsMetadataFields
                        :custom-data="form.custom_data"
                        @update:custom-data="form.custom_data = $event"
                    />
                    <UiFormActions>
                        <UButton
                            :label="t('core.common.cancel')"
                            color="neutral"
                            variant="outline"
                            @click="handleClose"
                        />
                        <UButton
                            type="submit"
                            :label="t('core.common.create')"
                            :loading="isCreating"
                            :disabled="!form.name || !form.email"
                        />
                    </UiFormActions>
                </form>
            </UCard>
        </template>
    </UModal>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.create-form {
    @apply flex flex-col gap-4;
}
</style>
