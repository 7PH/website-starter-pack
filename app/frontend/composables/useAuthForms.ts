// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Composable for shared auth form logic between ModalAuth and login page.
 * Provides form state, validation, and password visibility toggles.
 */
export function useAuthForms() {
    const { t } = useI18n();
    const backendConfig = useBackendConfig();
    const minPasswordLength = computed(() => backendConfig.config?.password_min_length ?? 8);

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
        customData: {} as UserCustomData,
    });

    const forgotPasswordForm = reactive({
        email: '',
    });

    const resetPasswordForm = reactive({
        password: '',
        confirmPassword: '',
    });

    // Password visibility toggles
    const passwordVisibility = reactive({
        login: false,
        signup: false,
        signupConfirm: false,
        reset: false,
        resetConfirm: false,
    });

    // Loading and errors
    const isLoading = ref(false);
    const errors = ref<Record<string, string>>({});

    /** Run an op while flipping isLoading. Caller awaits the result. */
    async function withLoading<T>(op: () => Promise<T>): Promise<T> {
        isLoading.value = true;
        try {
            return await op();
        } finally {
            isLoading.value = false;
        }
    }

    // Clear all errors
    function clearErrors() {
        errors.value = {};
    }

    // Validation functions
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
        } else if (signupForm.password.length < minPasswordLength.value) {
            errors.value.password = t('core.auth.passwordTooShort', { minLength: minPasswordLength.value });
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
        } else if (resetPasswordForm.password.length < minPasswordLength.value) {
            errors.value.password = t('core.auth.passwordTooShort', { minLength: minPasswordLength.value });
        }
        if (resetPasswordForm.password !== resetPasswordForm.confirmPassword) {
            errors.value.confirmPassword = t('core.auth.passwordMismatch');
        }
        return Object.keys(errors.value).length === 0;
    }

    // Reset all forms to initial state
    function resetForms() {
        loginForm.email = '';
        loginForm.password = '';
        loginForm.rememberMe = false;

        signupForm.email = '';
        signupForm.password = '';
        signupForm.confirmPassword = '';
        signupForm.firstName = '';
        signupForm.lastName = '';
        signupForm.customData = {} as UserCustomData;

        forgotPasswordForm.email = '';

        resetPasswordForm.password = '';
        resetPasswordForm.confirmPassword = '';

        // Reset visibility
        passwordVisibility.login = false;
        passwordVisibility.signup = false;
        passwordVisibility.signupConfirm = false;
        passwordVisibility.reset = false;
        passwordVisibility.resetConfirm = false;

        clearErrors();
    }

    // Pre-fill email across forms
    function setEmail(email: string) {
        loginForm.email = email;
        signupForm.email = email;
        forgotPasswordForm.email = email;
    }

    return {
        // Forms
        loginForm,
        signupForm,
        forgotPasswordForm,
        resetPasswordForm,

        // Password visibility
        passwordVisibility,

        // State
        isLoading,
        errors,
        withLoading,

        // Validation
        validateLogin,
        validateSignup,
        validateForgotPassword,
        validateResetPassword,

        // Utilities
        clearErrors,
        resetForms,
        setEmail,
    };
}
