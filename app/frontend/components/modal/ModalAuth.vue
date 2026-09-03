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

const auth = useAuth();
const { t } = useI18n();
const accountActions = useAccountActions();
const { isOpen, options, close } = useStoreModal<AuthModalOptions>(MODAL_NAME);

const mode = ref<AuthModalMode>('login');

const {
    usernamesEnabled,
    loginForm,
    signupForm,
    forgotPasswordForm,
    resetPasswordForm,
    passwordVisibility,
    isLoading,
    errors,
    validateLogin,
    validateSignup,
    validateForgotPassword,
    validateResetPassword,
    withLoading,
} = useAuthForms();

const signupMetadataRef = ref<{ validate: () => boolean } | null>(null);

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
            loginForm.identifier = opts.email;
            signupForm.email = opts.email;
            forgotPasswordForm.email = opts.email;
        }
    }
});

// Computed title
const title = computed(() => {
    if (auth.isLoggedIn) {
        return t('core.auth.account');
    }
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

function handleLogout() {
    accountActions.logout();
    close(false);
}

function validateSignupWithMetadata(): boolean {
    const baseValid = validateSignup();
    const metadataValid = signupMetadataRef.value?.validate() ?? true;
    return baseValid && metadataValid;
}

function onAuthSuccess() {
    options.value.onSuccess?.();
    close(true);
}

async function handleLogin() {
    if (!validateLogin()) return;
    if (await withLoading(() => accountActions.login(loginForm.identifier, loginForm.password))) {
        onAuthSuccess();
    }
}

async function handleSignup() {
    if (!validateSignupWithMetadata()) return;
    const success = await withLoading(() =>
        accountActions.signup(
            signupForm.email,
            signupForm.password,
            signupForm.firstName,
            signupForm.lastName,
            signupForm.customData,
            usernamesEnabled.value ? signupForm.username.trim() : undefined,
        ),
    );
    if (success) onAuthSuccess();
}

async function handleForgotPassword() {
    if (!validateForgotPassword()) return;
    await withLoading(() => accountActions.requestPasswordReset(forgotPasswordForm.email));
    mode.value = 'login';
}

async function handleResetPassword() {
    if (!validateResetPassword()) return;
    const token = options.value.resetToken;
    if (!token) {
        errors.value.general = t('core.auth.invalidResetLink');
        return;
    }
    if (await withLoading(() => accountActions.resetPassword(token, resetPasswordForm.password))) {
        close(true);
    }
}

function switchMode(newMode: AuthModalMode) {
    mode.value = newMode;
    errors.value = {};
}
</script>

<template>
    <UModal v-model:open="isOpen" :title="title" class="sm:max-w-md">
        <template #body>
            <!-- Logged In View -->
            <div v-if="auth.isLoggedIn" class="flex flex-col gap-5">
                <div class="text-center">
                    <div
                        class="w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center mx-auto mb-3"
                    >
                        <UIcon name="i-lucide-user" class="w-8 h-8 text-primary-500" />
                    </div>
                    <p class="font-medium text-gray-900 dark:text-gray-100">
                        {{ auth.user?.first_name }} {{ auth.user?.last_name }}
                    </p>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        {{ auth.user?.email }}
                    </p>
                </div>

                <div class="border-t border-gray-200 dark:border-gray-700 my-2" />

                <UButton
                    :label="t('core.auth.logout')"
                    color="error"
                    variant="soft"
                    icon="i-lucide-log-out"
                    block
                    @click="handleLogout"
                />
            </div>

            <template v-else>
                <!-- OAuth Buttons (shown for login and signup modes) -->
                <AuthOAuthButtons v-if="mode === 'login' || mode === 'signup'" />

                <!-- Login Form -->
                <form v-if="mode === 'login'" class="flex flex-col gap-5" @submit.prevent="handleLogin">
                    <UFormField
                        :label="usernamesEnabled ? t('core.auth.usernameOrEmail') : t('core.auth.email')"
                        :error="errors.identifier"
                    >
                        <UInput
                            v-model="loginForm.identifier"
                            :type="usernamesEnabled ? 'text' : 'email'"
                            :autocomplete="usernamesEnabled ? 'username' : 'email'"
                            :placeholder="usernamesEnabled ? t('core.auth.usernameOrEmail') : t('core.auth.email')"
                            :color="errors.identifier ? 'error' : undefined"
                            class="w-full"
                        />
                    </UFormField>

                    <UFormField :label="t('core.auth.password')" :error="errors.password">
                        <UInput
                            v-model="loginForm.password"
                            :type="passwordVisibility.login ? 'text' : 'password'"
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
                                    :icon="passwordVisibility.login ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                    :aria-label="
                                        passwordVisibility.login
                                            ? t('core.auth.hidePassword')
                                            : t('core.auth.showPassword')
                                    "
                                    @click="passwordVisibility.login = !passwordVisibility.login"
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

                    <UFormField
                        v-if="usernamesEnabled"
                        :label="t('core.auth.username')"
                        :error="errors.username"
                        :help="t('core.auth.usernameHelp')"
                    >
                        <UInput
                            v-model="signupForm.username"
                            type="text"
                            autocomplete="username"
                            :placeholder="t('core.auth.username')"
                            :color="errors.username ? 'error' : undefined"
                            class="w-full"
                        />
                    </UFormField>

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
                            :type="passwordVisibility.signup ? 'text' : 'password'"
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
                                    :icon="passwordVisibility.signup ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                    @click="passwordVisibility.signup = !passwordVisibility.signup"
                                />
                            </template>
                        </UInput>
                    </UFormField>

                    <UFormField :label="t('core.auth.confirmPassword')" :error="errors.confirmPassword">
                        <UInput
                            v-model="signupForm.confirmPassword"
                            :type="passwordVisibility.signupConfirm ? 'text' : 'password'"
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
                                    :icon="passwordVisibility.signupConfirm ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                    @click="passwordVisibility.signupConfirm = !passwordVisibility.signupConfirm"
                                />
                            </template>
                        </UInput>
                    </UFormField>

                    <UsersSignupMetadataFields
                        ref="signupMetadataRef"
                        :custom-data="signupForm.customData"
                        @update:custom-data="signupForm.customData = $event"
                        @validate="(metaErrors) => Object.assign(errors, metaErrors)"
                    />

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
                <form
                    v-else-if="mode === 'forgot-password'"
                    class="flex flex-col gap-5"
                    @submit.prevent="handleForgotPassword"
                >
                    <UAlert
                        color="info"
                        :title="t('core.auth.passwordResetTitle')"
                        :description="t('core.auth.forgotPasswordMessage')"
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

                    <UButton type="submit" :label="t('core.auth.sendResetLink')" :loading="isLoading" block />

                    <div class="border-t border-gray-200 dark:border-gray-700 my-2" />

                    <p class="text-center">
                        <UButton
                            :label="t('core.auth.backToLogin')"
                            variant="link"
                            color="neutral"
                            @click="switchMode('login')"
                        />
                    </p>
                </form>

                <!-- Reset Password Form -->
                <form
                    v-else-if="mode === 'reset-password'"
                    class="flex flex-col gap-5"
                    @submit.prevent="handleResetPassword"
                >
                    <UAlert v-if="errors.general" color="error" :title="errors.general" />

                    <UFormField :label="t('core.auth.password')" :error="errors.password">
                        <UInput
                            v-model="resetPasswordForm.password"
                            :type="passwordVisibility.reset ? 'text' : 'password'"
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
                                    :icon="passwordVisibility.reset ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                    @click="passwordVisibility.reset = !passwordVisibility.reset"
                                />
                            </template>
                        </UInput>
                    </UFormField>

                    <UFormField :label="t('core.auth.confirmPassword')" :error="errors.confirmPassword">
                        <UInput
                            v-model="resetPasswordForm.confirmPassword"
                            :type="passwordVisibility.resetConfirm ? 'text' : 'password'"
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
                                    :icon="passwordVisibility.resetConfirm ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                                    @click="passwordVisibility.resetConfirm = !passwordVisibility.resetConfirm"
                                />
                            </template>
                        </UInput>
                    </UFormField>

                    <UButton type="submit" :label="t('core.auth.resetPassword')" :loading="isLoading" block />
                </form>
            </template>
        </template>
    </UModal>
</template>
