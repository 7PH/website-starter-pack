<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script lang="ts" setup>
const props = defineProps<{
    open: boolean;
    isCreating: boolean;
}>();

const emit = defineEmits<{
    'update:open': [value: boolean];
    create: [data: { name: string; email: string; description: string }];
    close: [];
}>();

const form = ref({
    name: '',
    email: '',
    description: '',
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
    form.value = { name: '', email: '', description: '' };
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
                    <UiModalHeader title="Create Organization" @close="handleClose" />
                </template>

                <form class="create-form" @submit.prevent="handleSubmit">
                    <UFormField label="Name" required>
                        <UInput v-model="form.name" placeholder="Organization name" class="w-full" />
                    </UFormField>
                    <UFormField label="Email" required>
                        <UInput v-model="form.email" type="email" placeholder="contact@example.com" class="w-full" />
                    </UFormField>
                    <UFormField label="Description">
                        <UTextarea
                            v-model="form.description"
                            placeholder="Optional description..."
                            :rows="3"
                            class="w-full"
                        />
                    </UFormField>
                    <UiFormActions>
                        <UButton label="Cancel" color="neutral" variant="outline" @click="handleClose" />
                        <UButton
                            type="submit"
                            label="Create"
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
