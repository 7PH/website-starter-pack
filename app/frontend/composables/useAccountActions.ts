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
        // Status -> i18n key, for codes with one unambiguous cause on that endpoint.
        statusKeys?: Record<number, string>,
    ): Promise<boolean> {
        try {
            const result = await op();
            showSuccess(t(successKey));
            onSuccess?.(result);
            return true;
        } catch (error) {
            const mapped = statusKeys?.[getErrorStatus(error) ?? 0];
            if (mapped) {
                showError(new Error(t(mapped)), mapped);
            } else {
                showError(error, errorKey);
            }
            return false;
        }
    }

    // ============================================
    // Auth Actions (from useAuthActions)
    // ============================================

    /**
     * Login with an identifier (email, or username when usernames are enabled).
     */
    async function login(identifier: string, password: string): Promise<boolean> {
        const usernamesEnabled = useBackendConfig().config?.usernames_enabled === true;
        const invalidKey = usernamesEnabled ? 'core.auth.invalidCredentialsUsername' : 'core.auth.invalidCredentials';
        return withToast(
            () => usersApi.login(identifier, password),
            'core.auth.loginSuccess',
            invalidKey,
            (data) => auth.saveUserToken(data),
            // The server's detail would otherwise win over the fallback key and
            // reach the user in English.
            { 401: invalidKey },
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
        username?: string,
    ): Promise<boolean> {
        return withToast(
            () =>
                usersApi.signup({
                    email,
                    password,
                    first_name: firstName,
                    last_name: lastName,
                    custom_data: customData,
                    ...(username ? { username } : {}),
                }),
            'core.auth.registerSuccess',
            'core.errors.generic',
            (response) => {
                auth.saveUserToken(response);
                // Trigger email verification send (fire and forget)
                sendVerificationEmail().catch(() => {});
            },
            // A 409 here is either field, and the response can't say which, so the
            // message names both. Without usernames it can only be the email, and
            // the server's own wording is left alone.
            username ? { 409: 'core.auth.signupConflict' } : undefined,
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

        showSuccess(t('core.auth.passwordResetSent'), t('core.auth.passwordResetSentDescription'));
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
    async function updateProfile(
        firstName: string,
        lastName: string,
        customData?: UserCustomData,
        username?: string,
    ): Promise<boolean> {
        return withToast(
            () =>
                usersApi.updateProfile({
                    first_name: firstName,
                    last_name: lastName,
                    custom_data: customData,
                    ...(username ? { username } : {}),
                }),
            'core.account.profileSaved',
            'core.errors.generic',
            (updated) => auth.updateUser(updated),
            // The only 409 here is a taken handle; email changes use another route.
            { 409: 'core.auth.usernameTaken' },
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
