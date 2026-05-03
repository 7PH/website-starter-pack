// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Composable for account actions (auth + user operations).
 * Combines authentication flows and user profile management.
 * Handles UI concerns: toasts, store updates, error handling.
 */

import * as authApi from '~/utils/api/auth';
import * as usersApi from '~/utils/api/users';

export function useAccountActions() {
    const auth = useAuth();
    const { t } = useI18n();
    const { showSuccess, showError } = useToastHelpers();

    /** Run an API call, toast success/error, return true on success. */
    async function withToast<T>(
        op: () => Promise<T>,
        successKey: string,
        errorKey = 'core.errors.generic',
        onSuccess?: (result: T) => void,
    ): Promise<boolean> {
        try {
            const result = await op();
            showSuccess(t(successKey));
            onSuccess?.(result);
            return true;
        } catch (error) {
            showError(error, errorKey);
            return false;
        }
    }

    // ============================================
    // Auth Actions (from useAuthActions)
    // ============================================

    /**
     * Login with email and password.
     */
    async function login(email: string, password: string): Promise<boolean> {
        return withToast(
            () => usersApi.login(email, password),
            'core.auth.loginSuccess',
            'core.auth.invalidCredentials',
            (data) => auth.saveUserToken(data),
        );
    }

    /**
     * Register a new user.
     */
    async function signup(
        email: string,
        password: string,
        firstName: string,
        lastName: string,
        customData?: UserCustomData,
    ): Promise<boolean> {
        return withToast(
            () =>
                usersApi.signup({
                    email,
                    password,
                    first_name: firstName,
                    last_name: lastName,
                    custom_data: customData,
                }),
            'core.auth.registerSuccess',
            'core.errors.generic',
            (response) => {
                auth.saveUserToken(response);
                // Trigger email verification send (fire and forget)
                sendVerificationEmail().catch(() => {});
            },
        );
    }

    /**
     * Request password reset email.
     * Always shows success to prevent email enumeration.
     */
    async function requestPasswordReset(email: string): Promise<boolean> {
        try {
            await authApi.requestPasswordReset(email);
        } catch {
            // Ignore errors - always show success to prevent email enumeration
        }

        showSuccess(t('core.auth.passwordResetSent'));
        return true;
    }

    /**
     * Reset password with token from email link.
     */
    async function resetPassword(token: string, password: string): Promise<boolean> {
        return withToast(() => authApi.resetPassword(token, password), 'core.auth.passwordResetSuccess');
    }

    /**
     * Send email verification to current user.
     */
    async function sendVerificationEmail(): Promise<boolean> {
        try {
            await authApi.sendVerificationEmail();
            showSuccess(t('core.auth.verificationEmailSent'));
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
        return withToast(() => authApi.verifyEmail(token), 'core.auth.emailVerified');
    }

    /**
     * Confirm email change with token from email link.
     */
    async function confirmEmailChange(token: string): Promise<boolean> {
        return withToast(() => authApi.confirmEmailChange(token), 'core.account.email.changeSuccess');
    }

    /**
     * Logout and clear session.
     */
    function logout(): void {
        auth.logout();
        showSuccess(t('core.auth.logoutSuccess'));
        navigateTo('/');
    }

    // ============================================
    // User Actions (from useUserActions)
    // ============================================

    /**
     * Update user profile (first name, last name, optional custom_data).
     */
    async function updateProfile(firstName: string, lastName: string, customData?: UserCustomData): Promise<boolean> {
        return withToast(
            () => usersApi.updateProfile({ first_name: firstName, last_name: lastName, custom_data: customData }),
            'core.account.profileSaved',
            'core.errors.generic',
            (updated) => auth.updateUser(updated),
        );
    }

    /**
     * Request email change. Sends confirmation email to the new address.
     */
    async function requestEmailChange(newEmail: string, password: string): Promise<boolean> {
        return withToast(
            () => usersApi.requestEmailChange({ new_email: newEmail, password }),
            'core.account.email.verificationSent',
        );
    }

    /**
     * Change password.
     */
    async function changePassword(oldPassword: string, newPassword: string): Promise<boolean> {
        return withToast(
            () => usersApi.changePassword({ old_password: oldPassword, new_password: newPassword }),
            'core.account.password.changeSuccess',
        );
    }

    return {
        // Auth actions
        login,
        signup,
        requestPasswordReset,
        resetPassword,
        sendVerificationEmail,
        verifyEmail,
        confirmEmailChange,
        logout,

        // User actions
        updateProfile,
        requestEmailChange,
        changePassword,
    };
}
