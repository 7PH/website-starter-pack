<!-- ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack. -->
<script setup lang="ts">
definePageMeta({
    layout: 'auth',
});

const route = useRoute();
const auth = useAuth();
const accountActions = useAccountActions();
const { t } = useI18n();

type AuthMode = 'login' | 'signup' | 'forgot-password';
const initialMode = (route.query.mode as AuthMode) || 'login';
const mode = ref<AuthMode>(initialMode);
// Mirror the mode in the URL so a reload, the back button and the layout all see the same form.
const router = useRouter();
watch(mode, (m) => router.replace({ query: { ...route.query, mode: m } }));

onMounted(() => {
    if (auth.isLoggedIn) redirectAfterAuth();
});

const {
    usernamesEnabled,
    realNamesEnabled,
    loginForm,
    signupForm,
    forgotPasswordForm,
    isLoading,
    errors,
    validateLogin,
    validateSignup,
    validateForgotPassword,
    withLoading,
} = useAuthForms();

function redirectAfterAuth() {
    navigateTo((route.query.redirect as string) || '/');
}

const signupMetadataRef = ref<{ validate: () => boolean } | null>(null);

const title = computed(() => {
    switch (mode.value) {
        case 'login':
            return t('core.auth.login');
        case 'signup':
            return t('core.auth.register');
        case 'forgot-password':
            return t('core.auth.forgotPassword');
    }
});

function validateSignupWithMetadata(): boolean {
    const baseValid = validateSignup();
    signupMetadataRef.value?.validate(); // emits errors via @validate handler
    return baseValid && Object.keys(errors.value).length === 0;
}

// Actions
// Shown in the form rather than a toast, which screen readers may miss and which vanishes.
function showFormError(message: string) {
    errors.value.general = message;
}

async function handleLogin() {
    if (!validateLogin()) return;
    if (await withLoading(() => accountActions.login(loginForm.identifier, loginForm.password, showFormError))) {
        redirectAfterAuth();
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
            showFormError,
        ),
    );
    if (success) redirectAfterAuth();
}

async function handleForgotPassword() {
    if (!validateForgotPassword()) return;
    await withLoading(() => accountActions.requestPasswordReset(forgotPasswordForm.email));
    mode.value = 'login';
}

function switchMode(newMode: AuthMode) {
    mode.value = newMode;
    errors.value = {};
}
</script>

<template>
    <div>
        <h1 class="text-2xl font-bold mb-6 text-gradient-brand">{{ title }}</h1>

        <!-- OAuth Buttons (shown for login and signup modes) -->
        <AuthOAuthButtons v-if="mode === 'login' || mode === 'signup'" />

        <!-- Login Form -->
        <form v-if="mode === 'login'" class="flex flex-col gap-5" @submit.prevent="handleLogin">
            <UAlert v-if="errors.general" color="error" role="alert" :title="errors.general" />

            <UFormField
                :label="usernamesEnabled ? t('core.auth.usernameOrEmail') : t('core.auth.email')"
                :error="errors.identifier || !!errors.general"
            >
                <UInput
                    v-model="loginForm.identifier"
                    autofocus
                    :type="usernamesEnabled ? 'text' : 'email'"
                    :autocomplete="usernamesEnabled ? 'username' : 'email'"
                    :placeholder="usernamesEnabled ? t('core.auth.usernameOrEmail') : t('core.auth.email')"
                    :color="errors.identifier || errors.general ? 'error' : undefined"
                    class="w-full"
                />
            </UFormField>

            <UFormField :label="t('core.auth.password')" :error="errors.password || !!errors.general">
                <UiPasswordInput
                    v-model="loginForm.password"
                    autocomplete="current-password"
                    :placeholder="t('core.auth.password')"
                    :error="!!(errors.password || errors.general)"
                />
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

            <p class="text-center text-sm text-gray-500 dark:text-gray-400">
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
            <UAlert v-if="errors.general" color="error" role="alert" :title="errors.general" />

            <div v-if="realNamesEnabled" class="flex gap-3">
                <UFormField :label="t('core.auth.firstName')" :error="errors.firstName" class="flex-1">
                    <UInput
                        v-model="signupForm.firstName"
                        autofocus
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
                    :autofocus="!realNamesEnabled"
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
                    :autofocus="!realNamesEnabled && !usernamesEnabled"
                    type="email"
                    autocomplete="email"
                    :placeholder="t('core.auth.email')"
                    :color="errors.email ? 'error' : undefined"
                    class="w-full"
                />
            </UFormField>

            <UFormField :label="t('core.auth.password')" :error="errors.password">
                <UiPasswordInput
                    v-model="signupForm.password"
                    autocomplete="new-password"
                    :placeholder="t('core.auth.password')"
                    :error="!!errors.password"
                />
            </UFormField>

            <UFormField :label="t('core.auth.confirmPassword')" :error="errors.confirmPassword">
                <UiPasswordInput
                    v-model="signupForm.confirmPassword"
                    autocomplete="new-password"
                    :placeholder="t('core.auth.confirmPassword')"
                    :error="!!errors.confirmPassword"
                />
            </UFormField>

            <UsersSignupMetadataFields
                ref="signupMetadataRef"
                :custom-data="signupForm.customData"
                @update:custom-data="signupForm.customData = $event"
                @validate="(metaErrors) => Object.assign(errors, metaErrors)"
            />

            <UButton type="submit" :label="t('core.auth.createAccount')" :loading="isLoading" block />

            <div class="border-t border-gray-200 dark:border-gray-700 my-2" />

            <p class="text-center text-sm text-gray-500 dark:text-gray-400">
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
                :title="t('core.auth.forgotPassword')"
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
    </div>
</template>
