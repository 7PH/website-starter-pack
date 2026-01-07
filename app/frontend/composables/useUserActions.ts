// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Composable for user resource actions (/users/me/* endpoints).
 * Handles profile updates, password changes, and email change requests.
 */

interface AuthMessageResponse {
    message: string;
}

export function useUserActions() {
    const api = useApi();
    const auth = useAuth();
    const toast = useToast();
    const { t } = useI18n();

    /**
     * Update user profile (first name, last name).
     */
    async function updateProfile(firstName: string, lastName: string): Promise<boolean> {
        try {
            const updatedUser = await api.patch<UserRead>('/users/me', {
                first_name: firstName,
                last_name: lastName,
            });

            // Update stored user data with the response (no need for token refresh)
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
            await api.put<AuthMessageResponse>('/users/me/email', {
                new_email: newEmail,
                password,
            });

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
            await api.put<UserRead>('/users/me/password', {
                old_password: oldPassword,
                new_password: newPassword,
            });

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
        updateProfile,
        requestEmailChange,
        changePassword,
    };
}
