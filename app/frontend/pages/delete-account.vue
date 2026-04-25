<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
/**
 * Account deletion confirmation page.
 * Reads a deletion token from the URL fragment (#token) and finalizes the
 * deletion. Password users re-enter their password; OAuth users just confirm.
 * No authenticated session required — the token is the auth.
 */

import { confirmAccountDeletion, getAccountDeletionInfo } from '~/utils/api/auth';

const router = useRouter();
const auth = useAuth();
const { t } = useI18n();
const { showSuccess, showError } = useToastHelpers();

const status = ref<'loading' | 'ready' | 'invalid'>('loading');
const info = ref<AccountDeletionInfo | null>(null);
const token = ref<string | null>(null);
const password = ref('');
const showPassword = ref(false);
const isSubmitting = ref(false);
const passwordError = ref('');

onMounted(async () => {
    const hash = window.location.hash;
    token.value = hash ? hash.substring(1) : null;

    if (!token.value) {
        status.value = 'invalid';
        return;
    }

    try {
        info.value = await getAccountDeletionInfo(token.value);
        status.value = 'ready';
    } catch {
        status.value = 'invalid';
    }
});

async function confirmDeletion() {
    if (!token.value || !info.value) return;

    passwordError.value = '';
    if (info.value.requires_password && !password.value) {
        passwordError.value = t('core.validation.required');
        return;
    }

    isSubmitting.value = true;
    try {
        await confirmAccountDeletion(token.value, info.value.requires_password ? password.value : null);
        auth.logout();
        showSuccess(t('core.account.privacy.confirmPage.success'));
        router.push('/');
    } catch (error) {
        if (error instanceof Error && /password/i.test(error.message)) {
            passwordError.value = t('core.account.privacy.confirmPage.wrongPassword');
        } else {
            showError(error, 'core.account.privacy.confirmPage.failed');
        }
    } finally {
        isSubmitting.value = false;
    }
}
</script>

<template>
    <div class="min-h-screen flex items-center justify-center p-4">
        <UCard class="max-w-md w-full">
            <!-- Loading -->
            <div v-if="status === 'loading'" class="py-8 text-center">
                <UIcon name="i-lucide-loader-2" class="text-5xl text-primary-500 animate-spin" />
                <p class="mt-4 text-gray-600 dark:text-gray-400">{{ t('core.common.loading') }}</p>
            </div>

            <!-- Invalid / expired link -->
            <div v-else-if="status === 'invalid'" class="py-8 text-center">
                <UIcon name="i-lucide-x-circle" class="text-5xl text-red-500" />
                <h2 class="mt-4 text-xl font-semibold">{{ t('core.account.privacy.confirmPage.invalidTitle') }}</h2>
                <p class="mt-2 text-gray-600 dark:text-gray-400">
                    {{ t('core.account.privacy.confirmPage.invalidBody') }}
                </p>
                <UButton class="mt-4" :label="t('core.account.goHome')" @click="router.push('/')" />
            </div>

            <!-- Ready: confirm form -->
            <form v-else class="space-y-4" @submit.prevent="confirmDeletion">
                <div class="text-center">
                    <UIcon name="i-lucide-alert-triangle" class="text-5xl text-red-500" />
                    <h2 class="mt-4 text-xl font-semibold">{{ t('core.account.privacy.confirmPage.title') }}</h2>
                    <p class="mt-2 text-gray-600 dark:text-gray-400">
                        {{ t('core.account.privacy.confirmPage.warning', { email: info?.email_masked }) }}
                    </p>
                </div>

                <UFormField
                    v-if="info?.requires_password"
                    :label="t('core.account.privacy.confirmPage.passwordLabel')"
                    :error="passwordError"
                >
                    <UInput
                        v-model="password"
                        :type="showPassword ? 'text' : 'password'"
                        autocomplete="current-password"
                        :color="passwordError ? 'error' : undefined"
                        :ui="{ trailing: 'pe-1' }"
                        class="w-full"
                    >
                        <template #trailing>
                            <UButton
                                color="neutral"
                                variant="link"
                                size="sm"
                                :icon="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                @click="showPassword = !showPassword"
                            />
                        </template>
                    </UInput>
                </UFormField>

                <div class="flex justify-end gap-2 pt-2">
                    <UButton
                        color="neutral"
                        variant="ghost"
                        :label="t('core.common.cancel')"
                        :disabled="isSubmitting"
                        @click="router.push('/')"
                    />
                    <UButton
                        type="submit"
                        color="error"
                        icon="i-lucide-trash-2"
                        :label="t('core.account.privacy.confirmPage.deleteButton')"
                        :loading="isSubmitting"
                    />
                </div>
            </form>
        </UCard>
    </div>
</template>
