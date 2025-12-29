<script setup lang="ts">
/**
 * Email verification page.
 * Reads token from URL fragment (#token) and verifies email.
 */

const router = useRouter();
const authActions = useAuthActions();
const { t } = useI18n();

const status = ref<'loading' | 'success' | 'error'>('loading');
const errorMessage = ref('');

onMounted(async () => {
    // Get token from URL fragment
    const hash = window.location.hash;
    const token = hash ? hash.substring(1) : null;

    if (!token) {
        status.value = 'error';
        errorMessage.value = 'No verification token found';
        return;
    }

    const success = await authActions.verifyEmail(token);

    if (success) {
        status.value = 'success';
        // Redirect to home after 3 seconds
        setTimeout(() => {
            router.push('/');
        }, 3000);
    } else {
        status.value = 'error';
        errorMessage.value = 'Invalid or expired verification link';
    }
});
</script>

<template>
    <div class="min-h-screen flex items-center justify-center p-4">
        <Card class="max-w-md w-full text-center">
            <template #content>
                <!-- Loading -->
                <div v-if="status === 'loading'" class="py-8">
                    <i class="pi pi-spin pi-spinner text-5xl text-primary-500"></i>
                    <p class="mt-4 text-gray-600 dark:text-gray-400">Verifying your email...</p>
                </div>

                <!-- Success -->
                <div v-else-if="status === 'success'" class="py-8">
                    <i class="pi pi-check-circle text-5xl text-green-500"></i>
                    <h2 class="mt-4 text-xl font-semibold">Email Verified!</h2>
                    <p class="mt-2 text-gray-600 dark:text-gray-400">
                        Your email has been successfully verified. Redirecting...
                    </p>
                </div>

                <!-- Error -->
                <div v-else class="py-8">
                    <i class="pi pi-times-circle text-5xl text-red-500"></i>
                    <h2 class="mt-4 text-xl font-semibold">Verification Failed</h2>
                    <p class="mt-2 text-gray-600 dark:text-gray-400">
                        {{ errorMessage }}
                    </p>
                    <Button class="mt-4" severity="primary" label="Go to Home" @click="router.push('/')" />
                </div>
            </template>
        </Card>
    </div>
</template>
