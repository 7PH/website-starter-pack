<script setup lang="ts">
// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
/**
 * OAuth callback page.
 * Handles the redirect from OAuth providers (Google) with the authorization code.
 * Exchanges the code for a JWT token and redirects to the dashboard.
 */

definePageMeta({
    layout: 'auth',
});

const route = useRoute();
const { t } = useI18n();
const oauth = useOAuth();

const status = ref<'loading' | 'error' | 'success'>('loading');
const errorMessage = ref('');

onMounted(async () => {
    const code = route.query.code as string | undefined;
    const state = route.query.state as string | undefined;
    const error = route.query.error as string | undefined;

    // Check for OAuth errors from Google
    if (error) {
        status.value = 'error';
        if (error === 'access_denied') {
            errorMessage.value = t('core.oauth.accessDenied');
        } else {
            errorMessage.value = t('core.oauth.errorCallback');
        }
        return;
    }

    // Validate required parameters
    if (!code || !state) {
        status.value = 'error';
        errorMessage.value = t('core.oauth.missingParams');
        return;
    }

    // Exchange code for token
    const success = await oauth.handleOAuthCallback(code, state);

    if (success) {
        status.value = 'success';
        // Small delay to show success state before redirect
        await new Promise((resolve) => setTimeout(resolve, 500));
        navigateTo('/');
    } else {
        status.value = 'error';
        errorMessage.value = t('core.oauth.errorCallback');
    }
});

function goToLogin() {
    oauth.clearOAuthState();
    navigateTo('/login');
}
</script>

<template>
    <div class="flex flex-col items-center justify-center gap-6 py-8">
        <!-- Loading State -->
        <template v-if="status === 'loading'">
            <div class="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                <UIcon name="i-lucide-loader-2" class="w-6 h-6 text-primary-500 animate-spin" />
            </div>
            <div class="text-center">
                <h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {{ t('core.oauth.signingIn') }}
                </h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {{ t('core.oauth.pleaseWait') }}
                </p>
            </div>
        </template>

        <!-- Success State -->
        <template v-else-if="status === 'success'">
            <div class="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                <UIcon name="i-lucide-check" class="w-6 h-6 text-green-500" />
            </div>
            <div class="text-center">
                <h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {{ t('core.oauth.success') }}
                </h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {{ t('core.oauth.redirecting') }}
                </p>
            </div>
        </template>

        <!-- Error State -->
        <template v-else-if="status === 'error'">
            <div class="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
                <UIcon name="i-lucide-x" class="w-6 h-6 text-red-500" />
            </div>
            <div class="text-center">
                <h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {{ t('core.oauth.errorTitle') }}
                </h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {{ errorMessage }}
                </p>
            </div>
            <UButton :label="t('core.auth.backToLogin')" variant="soft" @click="goToLogin" />
        </template>
    </div>
</template>
