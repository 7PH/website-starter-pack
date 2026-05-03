<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
/**
 * Email verification page.
 * Reads token from URL fragment (#token) and verifies email.
 */

const router = useRouter();
const accountActions = useAccountActions();
const { t } = useI18n();

const { status, errorMessage } = useHashTokenAction({
    action: accountActions.verifyEmail,
    noTokenMessage: t('core.auth.noVerificationToken'),
    invalidMessage: t('core.auth.invalidVerificationLink'),
    onSuccess: () => setTimeout(() => router.push('/'), 3000),
});
</script>

<template>
    <div class="min-h-screen flex items-center justify-center p-4">
        <UCard class="max-w-md w-full text-center">
            <!-- Loading -->
            <div v-if="status === 'loading'" class="py-8">
                <UIcon name="i-lucide-loader-2" class="text-5xl text-primary-500 animate-spin" />
                <p class="mt-4 text-gray-600 dark:text-gray-400">{{ t('core.auth.verifyingEmail') }}</p>
            </div>

            <!-- Success -->
            <div v-else-if="status === 'success'" class="py-8">
                <UIcon name="i-lucide-check-circle" class="text-5xl text-green-500" />
                <h2 class="mt-4 text-xl font-semibold">{{ t('core.auth.emailVerifiedTitle') }}</h2>
                <p class="mt-2 text-gray-600 dark:text-gray-400">
                    {{ t('core.auth.emailVerifiedDescription') }}
                </p>
            </div>

            <!-- Error -->
            <div v-else class="py-8">
                <UIcon name="i-lucide-x-circle" class="text-5xl text-red-500" />
                <h2 class="mt-4 text-xl font-semibold">{{ t('core.auth.verificationFailed') }}</h2>
                <p class="mt-2 text-gray-600 dark:text-gray-400">
                    {{ errorMessage }}
                </p>
                <UButton class="mt-4" :label="t('core.common.goToHome')" @click="router.push('/')" />
            </div>
        </UCard>
    </div>
</template>
