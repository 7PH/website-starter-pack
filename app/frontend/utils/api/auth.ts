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
    return useApi().post<AuthMessageResponse>('/auth/send-verification-email', {});
}

/**
 * Verify email with token from verification email.
 */
export async function verifyEmail(token: string): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/auth/verify-email', { token });
}

/**
 * Request password reset email.
 */
export async function requestPasswordReset(email: string): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/auth/request-password-reset', { email });
}

/**
 * Reset password using token from reset email.
 */
export async function resetPassword(token: string, password: string): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/auth/reset-password', { token, password });
}

/**
 * Confirm email change using token from confirmation email.
 */
export async function confirmEmailChange(token: string): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/auth/confirm-email-change', { token });
}
