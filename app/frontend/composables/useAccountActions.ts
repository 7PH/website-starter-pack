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

    // ============================================
    // Auth Actions (from useAuthActions)
    // ============================================

    /**
     * Login with email and password.
     */
    async function login(email: string, password: string): Promise<boolean> {
        try {
            const data = await usersApi.login(email, password);
            auth.saveUserToken(data);
            showSuccess(t('core.auth.loginSuccess'));
            return true;
        } catch (error) {
            showError(error, 'core.auth.invalidCredentials');
            return false;
        }
    }

    /**
     * Register a new user.
     */
    async function signup(email: string, password: string, firstName: string, lastName: string): Promise<boolean> {
        try {
            const response = await usersApi.signup({
                email,
                password,
                first_name: firstName,
                last_name: lastName,
            });
            auth.saveUserToken(response);
            showSuccess(t('core.auth.registerSuccess'));

            // Trigger email verification send (fire and forget)
            sendVerificationEmail().catch(() => {});

            return true;
        } catch (error) {
            showError(error, 'core.errors.generic');
            return false;
        }
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
        try {
            await authApi.resetPassword(token, password);
            showSuccess(t('core.auth.passwordResetSuccess'));
            return true;
        } catch (error) {
            showError(error, 'core.errors.generic');
            return false;
        }
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
        try {
            await authApi.verifyEmail(token);
            showSuccess(t('core.auth.emailVerified'));
            return true;
        } catch (error) {
            showError(error, 'core.errors.generic');
            return false;
        }
    }

    /**
     * Confirm email change with token from email link.
     */
    async function confirmEmailChange(token: string): Promise<boolean> {
        try {
            await authApi.confirmEmailChange(token);
            showSuccess(t('core.account.email.changeSuccess'));
            return true;
        } catch (error) {
            showError(error, 'core.errors.generic');
            return false;
        }
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
     * Update user profile (first name, last name).
     */
    async function updateProfile(firstName: string, lastName: string): Promise<boolean> {
        try {
            const updatedUser = await usersApi.updateProfile({
                first_name: firstName,
                last_name: lastName,
            });
            auth.updateUser(updatedUser);
            showSuccess(t('core.account.profileSaved'));
            return true;
        } catch (error) {
            showError(error, 'core.errors.generic');
            return false;
        }
    }

    /**
     * Request email change. Sends confirmation email to the new address.
     */
    async function requestEmailChange(newEmail: string, password: string): Promise<boolean> {
        try {
            await usersApi.requestEmailChange({ new_email: newEmail, password });
            showSuccess(t('core.account.email.verificationSent'));
            return true;
        } catch (error) {
            showError(error, 'core.errors.generic');
            return false;
        }
    }

    /**
     * Change password.
     */
    async function changePassword(oldPassword: string, newPassword: string): Promise<boolean> {
        try {
            await usersApi.changePassword({ old_password: oldPassword, new_password: newPassword });
            showSuccess(t('core.account.password.changeSuccess'));
            return true;
        } catch (error) {
            showError(error, 'core.errors.generic');
            return false;
        }
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
