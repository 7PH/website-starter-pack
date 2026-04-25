// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Auth API service - mirrors backend/controllers/auth.py
 * Raw API calls without UI concerns (no toasts, no store updates).
 */

/**
 * Send email verification to current user.
 * Requires authentication.
 */
export async function sendVerificationEmail(): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/email-verifications', {});
}

/**
 * Verify email with token from verification email.
 */
export async function verifyEmail(token: string): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/email-verifications/confirm', { token });
}

/**
 * Request password reset email.
 */
export async function requestPasswordReset(email: string): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/password-resets', { email });
}

/**
 * Reset password using token from reset email.
 */
export async function resetPassword(token: string, password: string): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/password-resets/confirm', { token, password });
}

/**
 * Confirm email change using token from confirmation email.
 */
export async function confirmEmailChange(token: string): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/email-changes/confirm', { token });
}

/**
 * Inspect an account-deletion token to render the confirm page.
 * Returns whether a password is required and the masked email of the target.
 */
export async function getAccountDeletionInfo(token: string): Promise<AccountDeletionInfo> {
    return useApi().get<AccountDeletionInfo>('/account-deletions/info', { token });
}

/**
 * Confirm account deletion using token from the deletion email.
 * Password is required for password-auth users; OAuth-only users pass null.
 */
export async function confirmAccountDeletion(token: string, password: string | null): Promise<void> {
    return useApi().post<void>('/account-deletions/confirm', { token, password });
}
