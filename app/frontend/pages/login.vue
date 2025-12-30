<script setup lang="ts">
definePageMeta({
    layout: 'auth',
});

const route = useRoute();
const auth = useAuth();
const authActions = useAuthActions();
const { t } = useI18n();

// Form modes
type AuthMode = 'login' | 'signup' | 'forgot-password';
const initialMode = (route.query.mode as AuthMode) || 'login';
const mode = ref<AuthMode>(initialMode);

// Redirect if already logged in
onMounted(() => {
    if (auth.isLoggedIn) {
        const redirectTo = (route.query.redirect as string) || '/';
        navigateTo(redirectTo);
    }
});

// Loading and errors
const isLoading = ref(false);
const errors = ref<Record<string, string>>({});

// Password visibility toggles
const showLoginPassword = ref(false);
const showSignupPassword = ref(false);
const showSignupConfirmPassword = ref(false);

// Login form
const loginForm = reactive({
    email: '',
    password: '',
    rememberMe: false,
});

// Signup form
const signupForm = reactive({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
});

// Forgot password form
const forgotPasswordForm = reactive({
    email: '',
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

// Actions
async function handleLogin() {
    if (!validateLogin()) return;

    isLoading.value = true;
    const success = await authActions.login(loginForm.email, loginForm.password);
    isLoading.value = false;

    if (success) {
        const redirectTo = (route.query.redirect as string) || '/';
        navigateTo(redirectTo);
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
        const redirectTo = (route.query.redirect as string) || '/';
        navigateTo(redirectTo);
    }
}

async function handleForgotPassword() {
    if (!validateForgotPassword()) return;

    isLoading.value = true;
    await authActions.requestPasswordReset(forgotPasswordForm.email);
    isLoading.value = false;

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
