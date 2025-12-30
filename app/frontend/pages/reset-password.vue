<script setup lang="ts">
/**
 * Password reset page.
 * Reads token from URL fragment (#token) and opens reset modal.
 */

const modal = useModalStore();
const router = useRouter();

const status = ref<'loading' | 'ready' | 'no-token'>('loading');

onMounted(async () => {
    // Get token from URL fragment
    const hash = window.location.hash;
    const token = hash ? hash.substring(1) : null;

    if (!token) {
        status.value = 'no-token';
        return;
    }

    status.value = 'ready';

    // Open auth modal in reset-password mode
    const result = await modal.open<boolean>('auth', {
        initialMode: 'reset-password',
        resetToken: token,
    });

    if (result) {
        // Success - redirect to home
        router.push('/');
    }
});
</script>

<template>
    <div class="min-h-screen flex items-center justify-center p-4">
        <UCard v-if="status === 'no-token'" class="max-w-md w-full text-center">
            <div class="py-8">
                <UIcon name="i-lucide-x-circle" class="text-5xl text-red-500" />
                <h2 class="mt-4 text-xl font-semibold">Invalid Reset Link</h2>
                <p class="mt-2 text-gray-600 dark:text-gray-400">
                    This password reset link is invalid or has expired.
                </p>
                <UButton class="mt-4" label="Go to Home" @click="router.push('/')" />
            </div>
        </UCard>

        <!-- Modal will render when token is present -->
        <div v-else class="text-center">
            <p class="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
    </div>
</template>
