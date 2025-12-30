<script setup lang="ts">
// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { ModalOptions } from '~/types/modal';

type AuthModalMode = 'login' | 'signup' | 'forgot-password' | 'reset-password';

interface AuthModalOptions extends ModalOptions {
    initialMode?: AuthModalMode;
    email?: string;
    resetToken?: string;
    onSuccess?: () => void;
    redirectTo?: string;
}

const MODAL_NAME = 'auth';

const modal = useModalStore();
const { t } = useI18n();
const authActions = useAuthActions();

// Register on mount
onMounted(() => {
    modal.register(MODAL_NAME);
});

onUnmounted(() => {
    modal.unregister(MODAL_NAME);
});

// Modal state - use safe accessors (handle SSR and initialization)
const isOpen = computed({
    get: () => {
        if (import.meta.server) return false;
        return modal.isOpen?.(MODAL_NAME) ?? false;
    },
    set: (value: boolean) => {
        if (!value) close();
    },
});

const options = computed((): AuthModalOptions => {
    if (import.meta.server) return {} as AuthModalOptions;
    return (modal.getOptions?.(MODAL_NAME) ?? {}) as AuthModalOptions;
});

// Internal state
const mode = ref<AuthModalMode>('login');
const isLoading = ref(false);

// Password visibility toggles
const showLoginPassword = ref(false);
const showSignupPassword = ref(false);
const showSignupConfirmPassword = ref(false);
const showResetPassword = ref(false);
const showResetConfirmPassword = ref(false);

// Form data
const loginForm = reactive({
    email: '',
    password: '',
    rememberMe: false,
});

const signupForm = reactive({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
});

const forgotPasswordForm = reactive({
    email: '',
});

const resetPasswordForm = reactive({
    password: '',
    confirmPassword: '',
});

// Validation errors
const errors = ref<Record<string, string>>({});

// Reset forms when modal opens
watch(isOpen, (open) => {
    if (open) {
        // Reset to initial mode or default
        const opts = options.value;
        mode.value = opts?.initialMode || 'login';
        errors.value = {};
        isLoading.value = false;

        // Pre-fill email if provided
        if (opts?.email) {
            loginForm.email = opts.email;
            signupForm.email = opts.email;
            forgotPasswordForm.email = opts.email;
        }
    }
});

// Computed title
const title = computed(() => {
    switch (mode.value) {
        case 'login':
            return t('core.auth.login');
        case 'signup':
            return t('core.auth.register');
        case 'forgot-password':
            return t('core.auth.forgotPassword');
        case 'reset-password':
            return t('core.auth.resetPassword');
    }
});

// Validation
function validateLogin(): boolean {
    errors.value = {};
    if (!loginForm.email) {
        errors.value.email = t('core.validation.required');
    }
    if (!loginForm.password) {
        errors.value.password = t('core.validation.required');
    }
    return Object.keys(errors.value).length === 0;
}

function validateSignup(): boolean {
    errors.value = {};
    if (!signupForm.email) {
        errors.value.email = t('core.validation.required');
    }
    if (!signupForm.firstName) {
        errors.value.firstName = t('core.validation.required');
    }
    if (!signupForm.lastName) {
        errors.value.lastName = t('core.validation.required');
    }
    if (!signupForm.password) {
        errors.value.password = t('core.validation.required');
    } else if (signupForm.password.length < 8) {
        errors.value.password = t('core.auth.passwordTooShort');
    }
    if (signupForm.password !== signupForm.confirmPassword) {
        errors.value.confirmPassword = t('core.auth.passwordMismatch');
    }
    return Object.keys(errors.value).length === 0;
}

function validateForgotPassword(): boolean {
    errors.value = {};
    if (!forgotPasswordForm.email) {
        errors.value.email = t('core.validation.required');
    }
    return Object.keys(errors.value).length === 0;
}

function validateResetPassword(): boolean {
    errors.value = {};
    if (!resetPasswordForm.password) {
        errors.value.password = t('core.validation.required');
    } else if (resetPasswordForm.password.length < 8) {
        errors.value.password = t('core.auth.passwordTooShort');
    }
    if (resetPasswordForm.password !== resetPasswordForm.confirmPassword) {
        errors.value.confirmPassword = t('core.auth.passwordMismatch');
    }
    return Object.keys(errors.value).length === 0;
}

// Actions
async function handleLogin() {
    if (!validateLogin()) return;

    isLoading.value = true;
    const success = await authActions.login(loginForm.email, loginForm.password);
    isLoading.value = false;

    if (success) {
        options.value.onSuccess?.();
        modal.close(MODAL_NAME, true);
    }
}

async function handleSignup() {
    if (!validateSignup()) return;

    isLoading.value = true;
    const success = await authActions.signup({
        email: signupForm.email,
        password: signupForm.password,
        firstName: signupForm.firstName,
        lastName: signupForm.lastName,
    });
    isLoading.value = false;

    if (success) {
        options.value.onSuccess?.();
        modal.close(MODAL_NAME, true);
    }
}

async function handleForgotPassword() {
    if (!validateForgotPassword()) return;

    isLoading.value = true;
    await authActions.requestPasswordReset(forgotPasswordForm.email);
    isLoading.value = false;

    // Switch back to login mode
    mode.value = 'login';
}

async function handleResetPassword() {
    if (!validateResetPassword()) return;

    const token = options.value.resetToken;
    if (!token) {
        errors.value.general = 'Missing reset token';
        return;
    }

    isLoading.value = true;
    const success = await authActions.resetPassword(token, resetPasswordForm.password);
    isLoading.value = false;

    if (success) {
        modal.close(MODAL_NAME, true);
    }
}

function switchMode(newMode: AuthModalMode) {
    mode.value = newMode;
    errors.value = {};
}

function close() {
    modal.close(MODAL_NAME, false);
}
</script>

<template>
    <UModal v-model:open="isOpen" :title="title" class="sm:max-w-md">
        <template #body>
            <!-- Login Form -->
            <form v-if="mode === 'login'" class="flex flex-col gap-5" @submit.prevent="handleLogin">
                <UFormField :label="t('core.auth.email')" :error="errors.email">
                    <UInput
                        v-model="loginForm.email"
                        type="email"
                        autocomplete="email"
                        :placeholder="t('core.auth.email')"
                        :color="errors.email ? 'error' : undefined"
                        class="w-full"
                    />
                </UFormField>

                <UFormField :label="t('core.auth.password')" :error="errors.password">
                    <UInput
                        v-model="loginForm.password"
                        :type="showLoginPassword ? 'text' : 'password'"
                        autocomplete="current-password"
                        :placeholder="t('core.auth.password')"
                        :color="errors.password ? 'error' : undefined"
                        :ui="{ trailing: 'pe-1' }"
                        class="w-full"
                    >
                        <template #trailing>
                            <UButton
                                color="neutral"
                                variant="link"
                                size="sm"
                                :icon="showLoginPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                :aria-label="showLoginPassword ? 'Hide password' : 'Show password'"
                                @click="showLoginPassword = !showLoginPassword"
                            />
                        </template>
                    </UInput>
                </UFormField>

                <div class="flex items-center justify-between">
                    <UCheckbox v-model="loginForm.rememberMe" :label="t('core.auth.rememberMe')" />
                    <UButton
                        :label="t('core.auth.forgotPassword')"
                        variant="link"
                        color="primary"
                        size="sm"
                        @click="switchMode('forgot-password')"
                    />
                </div>

                <UButton type="submit" :label="t('core.auth.login')" :loading="isLoading" block />

                <div class="border-t border-gray-200 dark:border-gray-700 my-2" />

                <p class="text-center text-sm text-gray-500">
                    {{ t('core.auth.noAccount') }}
                    <UButton
                        :label="t('core.auth.createAccount')"
                        variant="link"
                        color="primary"
                        size="sm"
                        @click="switchMode('signup')"
                    />
                </p>
            </form>

            <!-- Signup Form -->
            <form v-else-if="mode === 'signup'" class="flex flex-col gap-5" @submit.prevent="handleSignup">
                <div class="flex gap-3">
                    <UFormField :label="t('core.auth.firstName')" :error="errors.firstName" class="flex-1">
                        <UInput
                            v-model="signupForm.firstName"
                            autocomplete="given-name"
                            :placeholder="t('core.auth.firstName')"
                            :color="errors.firstName ? 'error' : undefined"
                            class="w-full"
                        />
                    </UFormField>

                    <UFormField :label="t('core.auth.lastName')" :error="errors.lastName" class="flex-1">
                        <UInput
                            v-model="signupForm.lastName"
                            autocomplete="family-name"
                            :placeholder="t('core.auth.lastName')"
                            :color="errors.lastName ? 'error' : undefined"
                            class="w-full"
                        />
                    </UFormField>
                </div>

                <UFormField :label="t('core.auth.email')" :error="errors.email">
                    <UInput
                        v-model="signupForm.email"
                        type="email"
                        autocomplete="email"
                        :placeholder="t('core.auth.email')"
                        :color="errors.email ? 'error' : undefined"
                        class="w-full"
                    />
                </UFormField>

                <UFormField :label="t('core.auth.password')" :error="errors.password">
                    <UInput
                        v-model="signupForm.password"
                        :type="showSignupPassword ? 'text' : 'password'"
                        autocomplete="new-password"
                        :placeholder="t('core.auth.password')"
                        :color="errors.password ? 'error' : undefined"
                        :ui="{ trailing: 'pe-1' }"
                        class="w-full"
                    >
                        <template #trailing>
                            <UButton
                                color="neutral"
                                variant="link"
                                size="sm"
                                :icon="showSignupPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                @click="showSignupPassword = !showSignupPassword"
                            />
                        </template>
                    </UInput>
                </UFormField>

                <UFormField :label="t('core.auth.confirmPassword')" :error="errors.confirmPassword">
                    <UInput
                        v-model="signupForm.confirmPassword"
                        :type="showSignupConfirmPassword ? 'text' : 'password'"
                        autocomplete="new-password"
                        :placeholder="t('core.auth.confirmPassword')"
                        :color="errors.confirmPassword ? 'error' : undefined"
                        :ui="{ trailing: 'pe-1' }"
                        class="w-full"
                    >
                        <template #trailing>
                            <UButton
                                color="neutral"
                                variant="link"
                                size="sm"
                                :icon="showSignupConfirmPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                @click="showSignupConfirmPassword = !showSignupConfirmPassword"
                            />
                        </template>
                    </UInput>
                </UFormField>

                <UButton type="submit" :label="t('core.auth.createAccount')" :loading="isLoading" block />

                <div class="border-t border-gray-200 dark:border-gray-700 my-2" />

                <p class="text-center text-sm text-gray-500">
                    {{ t('core.auth.hasAccount') }}
                    <UButton
                        :label="t('core.auth.login')"
                        variant="link"
                        color="primary"
                        size="sm"
                        @click="switchMode('login')"
                    />
                </p>
            </form>

            <!-- Forgot Password Form -->
            <form v-else-if="mode === 'forgot-password'" class="flex flex-col gap-5" @submit.prevent="handleForgotPassword">
                <UAlert
                    color="info"
                    title="Password Reset"
                    description="Enter your email address and we'll send you a link to reset your password."
                />

                <UFormField :label="t('core.auth.email')" :error="errors.email">
                    <UInput
                        v-model="forgotPasswordForm.email"
                        type="email"
                        autocomplete="email"
                        :placeholder="t('core.auth.email')"
                        :color="errors.email ? 'error' : undefined"
                        class="w-full"
                    />
                </UFormField>

                <UButton type="submit" label="Send Reset Link" :loading="isLoading" block />

                <div class="border-t border-gray-200 dark:border-gray-700 my-2" />

                <p class="text-center">
                    <UButton
                        :label="`Back to ${t('core.auth.login')}`"
                        variant="link"
                        color="neutral"
                        @click="switchMode('login')"
                    />
                </p>
            </form>

            <!-- Reset Password Form -->
            <form v-else-if="mode === 'reset-password'" class="flex flex-col gap-5" @submit.prevent="handleResetPassword">
                <UAlert v-if="errors.general" color="error" :title="errors.general" />

                <UFormField :label="t('core.auth.password')" :error="errors.password">
                    <UInput
                        v-model="resetPasswordForm.password"
                        :type="showResetPassword ? 'text' : 'password'"
                        autocomplete="new-password"
                        :placeholder="t('core.auth.password')"
                        :color="errors.password ? 'error' : undefined"
                        :ui="{ trailing: 'pe-1' }"
                        class="w-full"
                    >
                        <template #trailing>
                            <UButton
                                color="neutral"
                                variant="link"
                                size="sm"
                                :icon="showResetPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                @click="showResetPassword = !showResetPassword"
                            />
                        </template>
                    </UInput>
                </UFormField>

                <UFormField :label="t('core.auth.confirmPassword')" :error="errors.confirmPassword">
                    <UInput
                        v-model="resetPasswordForm.confirmPassword"
                        :type="showResetConfirmPassword ? 'text' : 'password'"
                        autocomplete="new-password"
                        :placeholder="t('core.auth.confirmPassword')"
                        :color="errors.confirmPassword ? 'error' : undefined"
                        :ui="{ trailing: 'pe-1' }"
                        class="w-full"
                    >
                        <template #trailing>
                            <UButton
                                color="neutral"
                                variant="link"
                                size="sm"
                                :icon="showResetConfirmPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                @click="showResetConfirmPassword = !showResetConfirmPassword"
                            />
                        </template>
                    </UInput>
                </UFormField>

                <UButton type="submit" :label="t('core.auth.resetPassword')" :loading="isLoading" block />
            </form>
        </template>
    </UModal>
</template>
