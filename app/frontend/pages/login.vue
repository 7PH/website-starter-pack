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
        <h1 class="text-2xl font-bold mb-6">{{ title }}</h1>

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
                {{ t('core.auth.forgotPasswordMessage') }}
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

            <Button type="submit" :label="t('core.auth.sendResetLink')" :loading="isLoading" class="w-full" />

            <Divider />

            <p class="text-center">
                <Button
                    :label="t('core.auth.backToLogin')"
                    link
                    severity="secondary"
                    type="button"
                    @click="switchMode('login')"
                />
            </p>
        </form>
    </div>
</template>
