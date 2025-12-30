// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Composable for authentication actions (login, signup, password reset, etc.)
 * Works with the useAuth store and useApi composable.
 */

interface AuthMessageResponse {
    message: string;
}

export function useAuthActions() {
    const api = useApi();
    const auth = useAuth();
    const toast = useToast();
    const { t } = useI18n();

    /**
     * Login with email and password.
     * Uses OAuth2 form format as expected by FastAPI.
     */
    async function login(email: string, password: string): Promise<boolean> {
        try {
            const basepath = useRuntimeConfig().public.apiBase;

            // FastAPI OAuth2 expects x-www-form-urlencoded format
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(basepath + '/users/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString(),
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Invalid credentials');
            }

            const data = (await response.json()) as UserTokenUpdate;
            auth.saveUserToken(data);
            toast.add({
                color: 'success',
                title: t('core.auth.loginSuccess'),
                duration: 3000,
            });
            return true;
        } catch (error) {
            const message = error instanceof Error ? error.message : t('core.auth.invalidCredentials');
            toast.add({
                color: 'error',
                title: t('core.errors.generic'),
                description: message,
                duration: 5000,
            });
            return false;
        }
    }

    /**
     * Register a new user.
     */
    async function signup(data: {
        email: string;
        password: string;
        firstName: string;
        lastName: string;
    }): Promise<boolean> {
        try {
            const response = await api.post<UserTokenUpdate>('/users', {
                email: data.email,
                password: data.password,
                first_name: data.firstName,
                last_name: data.lastName,
            });

            auth.saveUserToken(response);
            toast.add({
                color: 'success',
                title: t('core.auth.registerSuccess'),
                duration: 3000,
            });

            // Trigger email verification send (fire and forget)
            sendVerificationEmail().catch(() => {});

            return true;
        } catch (error) {
            const message = error instanceof Error ? error.message : t('core.errors.generic');
            toast.add({
                color: 'error',
                title: t('core.errors.generic'),
                description: message,
                duration: 5000,
            });
            return false;
        }
    }

    /**
     * Request password reset email.
     * Always shows success to prevent email enumeration.
     */
    async function requestPasswordReset(email: string): Promise<boolean> {
        try {
            await api.post<AuthMessageResponse>('/auth/request-password-reset', { email });
        } catch {
            // Ignore errors - always show success to prevent email enumeration
        }

        toast.add({
            color: 'success',
            title: t('core.auth.passwordResetSent'),
            duration: 3000,
        });
        return true;
    }

    /**
     * Reset password with token from email link.
     */
    async function resetPassword(token: string, password: string): Promise<boolean> {
        try {
            await api.post<AuthMessageResponse>('/auth/reset-password', { token, password });
            toast.add({
                color: 'success',
                title: t('core.auth.passwordResetSuccess'),
                duration: 3000,
            });
            return true;
        } catch (error) {
            const message = error instanceof Error ? error.message : t('core.errors.generic');
            toast.add({
                color: 'error',
                title: t('core.errors.generic'),
                description: message,
                duration: 5000,
            });
            return false;
        }
    }

    /**
     * Send email verification to current user.
     */
    async function sendVerificationEmail(): Promise<boolean> {
        try {
            await api.post<AuthMessageResponse>('/auth/send-verification-email', {});
            toast.add({
                color: 'success',
                title: t('core.auth.verificationEmailSent'),
                duration: 3000,
            });
            return true;
        } catch (error) {
            // Non-critical - just log
            console.error('Failed to send verification email:', error);
            return false;
        }
    }

    /**
     * Verify email with token from email link.
     */
    async function verifyEmail(token: string): Promise<boolean> {
        try {
            await api.post<AuthMessageResponse>('/auth/verify-email', { token });
            toast.add({
                color: 'success',
                title: t('core.auth.emailVerified'),
                duration: 3000,
            });
            return true;
        } catch (error) {
            const message = error instanceof Error ? error.message : t('core.errors.generic');
            toast.add({
                color: 'error',
                title: t('core.errors.generic'),
                description: message,
                duration: 5000,
            });
            return false;
        }
    }

    /**
     * Logout and clear session.
     */
    function logout(): void {
        auth.logout();
        toast.add({
            color: 'success',
            title: t('core.auth.logoutSuccess'),
            duration: 3000,
        });
    }

    return {
        login,
        signup,
        requestPasswordReset,
        resetPassword,
        sendVerificationEmail,
        verifyEmail,
        logout,
    };
}
