<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
/**
 * Email change confirmation page.
 * Reads token from URL fragment (#token) and confirms the email change.
 */

const router = useRouter();
const authActions = useAuthActions();
const auth = useAuth();
const { t } = useI18n();

const status = ref<'loading' | 'success' | 'error'>('loading');
const errorMessage = ref('');

onMounted(async () => {
    // Get token from URL fragment
    const hash = window.location.hash;
    const token = hash ? hash.substring(1) : null;

    if (!token) {
        status.value = 'error';
        errorMessage.value = t('core.account.email.noToken');
        return;
    }

    const success = await authActions.confirmEmailChange(token);

    if (success) {
        status.value = 'success';
        // Logout user since their email changed - they need to login with new email
        auth.logout();
        // Redirect to login after 3 seconds
        setTimeout(() => {
            router.push('/login');
        }, 3000);
    } else {
        status.value = 'error';
        errorMessage.value = t('core.account.email.invalidToken');
    }
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
