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
    const toast = useToast();
    const { t } = useI18n();

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
    async function signup(email: string, password: string, firstName: string, lastName: string): Promise<boolean> {
        try {
            const response = await usersApi.signup({
                email,
                password,
                first_name: firstName,
                last_name: lastName,
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
            await authApi.requestPasswordReset(email);
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
            await authApi.resetPassword(token, password);
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
            await authApi.sendVerificationEmail();
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
            await authApi.verifyEmail(token);
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
     * Confirm email change with token from email link.
     */
    async function confirmEmailChange(token: string): Promise<boolean> {
        try {
            await authApi.confirmEmailChange(token);
            toast.add({
                color: 'success',
                title: t('core.account.email.changeSuccess'),
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
            toast.add({
                color: 'success',
                title: t('core.account.profileSaved'),
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
     * Request email change. Sends confirmation email to the new address.
     */
    async function requestEmailChange(newEmail: string, password: string): Promise<boolean> {
        try {
            await usersApi.requestEmailChange({ new_email: newEmail, password });
            toast.add({
                color: 'success',
                title: t('core.account.email.verificationSent'),
                duration: 5000,
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
     * Change password.
     */
    async function changePassword(oldPassword: string, newPassword: string): Promise<boolean> {
        try {
            await usersApi.changePassword({ old_password: oldPassword, new_password: newPassword });
            toast.add({
                color: 'success',
                title: t('core.account.password.changeSuccess'),
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
