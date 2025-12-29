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
    <Dialog
        v-model:visible="isOpen"
        :header="title"
        modal
        :closable="true"
        :draggable="false"
        :style="{ width: '28rem' }"
        :pt="{
            root: { class: 'border-none' },
            header: { class: 'pb-2' },
            content: { class: 'pt-0' },
        }"
    >
        <!-- Login Form -->
        <form v-if="mode === 'login'" class="flex flex-col gap-5" @submit.prevent="handleLogin">
            <div class="flex flex-col gap-2">
                <label for="login-email" class="font-medium text-sm">{{ t('core.auth.email') }}</label>
                <InputText
                    id="login-email"
                    v-model="loginForm.email"
                    type="email"
                    autocomplete="email"
                    :placeholder="t('core.auth.email')"
                    :invalid="!!errors.email"
                    fluid
                />
                <small v-if="errors.email" class="text-red-500">{{ errors.email }}</small>
            </div>

            <div class="flex flex-col gap-2">
                <label for="login-password" class="font-medium text-sm">{{ t('core.auth.password') }}</label>
                <Password
                    id="login-password"
                    v-model="loginForm.password"
                    autocomplete="current-password"
                    :placeholder="t('core.auth.password')"
                    :invalid="!!errors.password"
                    :feedback="false"
                    toggle-mask
                    fluid
                />
                <small v-if="errors.password" class="text-red-500">{{ errors.password }}</small>
            </div>

            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <Checkbox v-model="loginForm.rememberMe" :binary="true" input-id="rememberMe" />
                    <label for="rememberMe" class="text-sm cursor-pointer">{{ t('core.auth.rememberMe') }}</label>
                </div>
                <Button
                    :label="t('core.auth.forgotPassword')"
                    link
                    type="button"
                    class="p-0 text-sm"
                    @click="switchMode('forgot-password')"
                />
            </div>

            <Button type="submit" :label="t('core.auth.login')" :loading="isLoading" class="w-full" />

            <Divider />

            <p class="text-center text-sm text-surface-500">
                {{ t('core.auth.noAccount') }}
                <Button
                    :label="t('core.auth.createAccount')"
                    link
                    type="button"
                    class="p-0 text-sm"
                    @click="switchMode('signup')"
                />
            </p>
        </form>

        <!-- Signup Form -->
        <form v-else-if="mode === 'signup'" class="flex flex-col gap-5" @submit.prevent="handleSignup">
            <div class="flex gap-3">
                <div class="flex flex-col gap-2 flex-1">
                    <label for="signup-firstname" class="font-medium text-sm">{{ t('core.auth.firstName') }}</label>
                    <InputText
                        id="signup-firstname"
                        v-model="signupForm.firstName"
                        autocomplete="given-name"
                        :placeholder="t('core.auth.firstName')"
                        :invalid="!!errors.firstName"
                        fluid
                    />
                    <small v-if="errors.firstName" class="text-red-500">{{ errors.firstName }}</small>
                </div>

                <div class="flex flex-col gap-2 flex-1">
                    <label for="signup-lastname" class="font-medium text-sm">{{ t('core.auth.lastName') }}</label>
                    <InputText
                        id="signup-lastname"
                        v-model="signupForm.lastName"
                        autocomplete="family-name"
                        :placeholder="t('core.auth.lastName')"
                        :invalid="!!errors.lastName"
                        fluid
                    />
                    <small v-if="errors.lastName" class="text-red-500">{{ errors.lastName }}</small>
                </div>
            </div>

            <div class="flex flex-col gap-2">
                <label for="signup-email" class="font-medium text-sm">{{ t('core.auth.email') }}</label>
                <InputText
                    id="signup-email"
                    v-model="signupForm.email"
                    type="email"
                    autocomplete="email"
                    :placeholder="t('core.auth.email')"
                    :invalid="!!errors.email"
                    fluid
                />
                <small v-if="errors.email" class="text-red-500">{{ errors.email }}</small>
            </div>

            <div class="flex flex-col gap-2">
                <label for="signup-password" class="font-medium text-sm">{{ t('core.auth.password') }}</label>
                <Password
                    id="signup-password"
                    v-model="signupForm.password"
                    autocomplete="new-password"
                    :placeholder="t('core.auth.password')"
                    :invalid="!!errors.password"
                    toggle-mask
                    fluid
                />
                <small v-if="errors.password" class="text-red-500">{{ errors.password }}</small>
            </div>

            <div class="flex flex-col gap-2">
                <label for="signup-confirm-password" class="font-medium text-sm">{{
                    t('core.auth.confirmPassword')
                }}</label>
                <Password
                    id="signup-confirm-password"
                    v-model="signupForm.confirmPassword"
                    autocomplete="new-password"
                    :placeholder="t('core.auth.confirmPassword')"
                    :invalid="!!errors.confirmPassword"
                    :feedback="false"
                    toggle-mask
                    fluid
                />
                <small v-if="errors.confirmPassword" class="text-red-500">{{ errors.confirmPassword }}</small>
            </div>

            <Button type="submit" :label="t('core.auth.createAccount')" :loading="isLoading" class="w-full" />

            <Divider />

            <p class="text-center text-sm text-surface-500">
                {{ t('core.auth.hasAccount') }}
                <Button
                    :label="t('core.auth.login')"
                    link
                    type="button"
                    class="p-0 text-sm"
                    @click="switchMode('login')"
                />
            </p>
        </form>

        <!-- Forgot Password Form -->
        <form v-else-if="mode === 'forgot-password'" class="flex flex-col gap-5" @submit.prevent="handleForgotPassword">
            <Message severity="info" :closable="false">
                Enter your email address and we'll send you a link to reset your password.
            </Message>

            <div class="flex flex-col gap-2">
                <label for="forgot-email" class="font-medium text-sm">{{ t('core.auth.email') }}</label>
                <InputText
                    id="forgot-email"
                    v-model="forgotPasswordForm.email"
                    type="email"
                    autocomplete="email"
                    :placeholder="t('core.auth.email')"
                    :invalid="!!errors.email"
                    fluid
                />
                <small v-if="errors.email" class="text-red-500">{{ errors.email }}</small>
            </div>

            <Button type="submit" label="Send Reset Link" :loading="isLoading" class="w-full" />

            <Divider />

            <p class="text-center">
                <Button
                    :label="`Back to ${t('core.auth.login')}`"
                    link
                    severity="secondary"
                    type="button"
                    @click="switchMode('login')"
                />
            </p>
        </form>

        <!-- Reset Password Form -->
        <form v-else-if="mode === 'reset-password'" class="flex flex-col gap-5" @submit.prevent="handleResetPassword">
            <Message v-if="errors.general" severity="error" :closable="false">
                {{ errors.general }}
            </Message>

            <div class="flex flex-col gap-2">
                <label for="reset-password" class="font-medium text-sm">{{ t('core.auth.password') }}</label>
                <Password
                    id="reset-password"
                    v-model="resetPasswordForm.password"
                    autocomplete="new-password"
                    :placeholder="t('core.auth.password')"
                    :invalid="!!errors.password"
                    toggle-mask
                    fluid
                />
                <small v-if="errors.password" class="text-red-500">{{ errors.password }}</small>
            </div>

            <div class="flex flex-col gap-2">
                <label for="reset-confirm-password" class="font-medium text-sm">{{
                    t('core.auth.confirmPassword')
                }}</label>
                <Password
                    id="reset-confirm-password"
                    v-model="resetPasswordForm.confirmPassword"
                    autocomplete="new-password"
                    :placeholder="t('core.auth.confirmPassword')"
                    :invalid="!!errors.confirmPassword"
                    :feedback="false"
                    toggle-mask
                    fluid
                />
                <small v-if="errors.confirmPassword" class="text-red-500">{{ errors.confirmPassword }}</small>
            </div>

            <Button type="submit" :label="t('core.auth.resetPassword')" :loading="isLoading" class="w-full" />
        </form>
    </Dialog>
</template>
