<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
const accountActions = useAccountActions();
const { t } = useI18n();

// Loading state
const isPasswordLoading = ref(false);

// Form errors
const passwordErrors = ref<Record<string, string>>({});

// Password visibility toggles
const showCurrentPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmPassword = ref(false);

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
    } else if (passwordForm.newPassword.length < 8) {
        passwordErrors.value.newPassword = t('core.auth.passwordTooShort');
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
                <UInput
                    v-model="passwordForm.currentPassword"
                    :type="showCurrentPassword ? 'text' : 'password'"
                    autocomplete="current-password"
                    :color="passwordErrors.currentPassword ? 'error' : undefined"
                    :ui="{ trailing: 'pe-1' }"
                    class="w-full"
                >
                    <template #trailing>
                        <UButton
                            color="neutral"
                            variant="link"
                            size="sm"
                            :icon="showCurrentPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                            @click="showCurrentPassword = !showCurrentPassword"
                        />
                    </template>
                </UInput>
            </UFormField>

            <UFormField :label="t('core.account.password.new')" :error="passwordErrors.newPassword">
                <UInput
                    v-model="passwordForm.newPassword"
                    :type="showNewPassword ? 'text' : 'password'"
                    autocomplete="new-password"
                    :color="passwordErrors.newPassword ? 'error' : undefined"
                    :ui="{ trailing: 'pe-1' }"
                    class="w-full"
                >
                    <template #trailing>
                        <UButton
                            color="neutral"
                            variant="link"
                            size="sm"
                            :icon="showNewPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                            @click="showNewPassword = !showNewPassword"
                        />
                    </template>
                </UInput>
            </UFormField>

            <UFormField :label="t('core.account.password.confirm')" :error="passwordErrors.confirmPassword">
                <UInput
                    v-model="passwordForm.confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    autocomplete="new-password"
                    :color="passwordErrors.confirmPassword ? 'error' : undefined"
                    :ui="{ trailing: 'pe-1' }"
                    class="w-full"
                >
                    <template #trailing>
                        <UButton
                            color="neutral"
                            variant="link"
                            size="sm"
                            :icon="showConfirmPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                            @click="showConfirmPassword = !showConfirmPassword"
                        />
                    </template>
                </UInput>
            </UFormField>

            <div class="flex justify-end">
                <UButton type="submit" :label="t('core.account.password.change')" :loading="isPasswordLoading" />
            </div>
        </form>
    </UCard>
</template>
