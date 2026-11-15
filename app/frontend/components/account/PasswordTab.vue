<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
const accountActions = useAccountActions();
const { t } = useI18n();
const backendConfig = useBackendConfig();
const minPasswordLength = computed(() => backendConfig.config?.password_min_length ?? 8);

// Loading state
const isPasswordLoading = ref(false);

// Form errors
const passwordErrors = ref<Record<string, string>>({});

// Password visibility toggles

// Password form
const passwordForm = reactive({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
});

// Validation
function validatePassword(): boolean {
    passwordErrors.value = {};
    if (!passwordForm.currentPassword) {
        passwordErrors.value.currentPassword = t('core.validation.required');
    }
    if (!passwordForm.newPassword) {
        passwordErrors.value.newPassword = t('core.validation.required');
    } else if (passwordForm.newPassword.length < minPasswordLength.value) {
        passwordErrors.value.newPassword = t('core.auth.passwordTooShort', { minLength: minPasswordLength.value });
    }
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
        passwordErrors.value.confirmPassword = t('core.auth.passwordMismatch');
    }
    return Object.keys(passwordErrors.value).length === 0;
}

// Action
async function handlePasswordChange() {
    if (!validatePassword()) return;

    isPasswordLoading.value = true;
    const success = await accountActions.changePassword(passwordForm.currentPassword, passwordForm.newPassword);
    isPasswordLoading.value = false;

    if (success) {
        passwordForm.currentPassword = '';
        passwordForm.newPassword = '';
        passwordForm.confirmPassword = '';
    }
}
</script>

<template>
    <UCard>
        <template #header>
            <div>
                <h2 class="text-lg font-semibold">{{ t('core.account.password.title') }}</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                    {{ t('core.account.password.description') }}
                </p>
            </div>
        </template>

        <form class="flex flex-col gap-4" @submit.prevent="handlePasswordChange">
            <UFormField :label="t('core.account.password.current')" :error="passwordErrors.currentPassword">
                <UiPasswordInput
                    v-model="passwordForm.currentPassword"
                    autocomplete="current-password"
                    :error="!!passwordErrors.currentPassword"
                />
            </UFormField>

            <UFormField :label="t('core.account.password.new')" :error="passwordErrors.newPassword">
                <UiPasswordInput
                    v-model="passwordForm.newPassword"
                    autocomplete="new-password"
                    :error="!!passwordErrors.newPassword"
                />
            </UFormField>

            <UFormField :label="t('core.account.password.confirm')" :error="passwordErrors.confirmPassword">
                <UiPasswordInput
                    v-model="passwordForm.confirmPassword"
                    autocomplete="new-password"
                    :error="!!passwordErrors.confirmPassword"
                />
            </UFormField>

            <div class="flex justify-end">
                <UButton type="submit" :label="t('core.account.password.change')" :loading="isPasswordLoading" />
            </div>
        </form>
    </UCard>
</template>
