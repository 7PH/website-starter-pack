<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
/**
 * Email change confirmation page.
 * Reads token from URL fragment (#token) and confirms the email change.
 */

const router = useRouter();
const accountActions = useAccountActions();
const auth = useAuth();
const { t } = useI18n();

const { status, errorMessage } = useHashTokenAction({
    action: accountActions.confirmEmailChange,
    noTokenMessage: t('core.account.email.noToken'),
    invalidMessage: t('core.account.email.invalidToken'),
    onSuccess: () => {
        // Email changed — force re-login with new address.
        auth.logout();
        setTimeout(() => router.push('/login'), 3000);
    },
});
</script>

<template>
    <div class="min-h-screen flex items-center justify-center p-4">
        <UCard class="max-w-md w-full text-center">
            <!-- Loading -->
            <div v-if="status === 'loading'" class="py-8">
                <UIcon name="i-lucide-loader-2" class="text-5xl text-primary-500 animate-spin" />
                <p class="mt-4 text-gray-600 dark:text-gray-400">{{ t('core.account.email.confirming') }}</p>
            </div>

            <!-- Success -->
            <div v-else-if="status === 'success'" class="py-8">
                <UIcon name="i-lucide-check-circle" class="text-5xl text-green-500" />
                <h2 class="mt-4 text-xl font-semibold">{{ t('core.account.email.changeSuccess') }}</h2>
                <p class="mt-2 text-gray-600 dark:text-gray-400">
                    {{ t('core.account.email.redirectingToLogin') }}
                </p>
            </div>

            <!-- Error -->
            <div v-else class="py-8">
                <UIcon name="i-lucide-x-circle" class="text-5xl text-red-500" />
                <h2 class="mt-4 text-xl font-semibold">{{ t('core.account.email.changeFailed') }}</h2>
                <p class="mt-2 text-gray-600 dark:text-gray-400">
                    {{ errorMessage }}
                </p>
                <UButton class="mt-4" :label="t('core.account.goHome')" @click="router.push('/')" />
            </div>
        </UCard>
    </div>
</template>
