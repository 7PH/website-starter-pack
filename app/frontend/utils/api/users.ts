// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Users API service - mirrors backend/controllers/users.py
 * Raw API calls without UI concerns (no toasts, no store updates).
 */

/**
 * Register a new user.
 */
export async function signup(data: UserCreate): Promise<UserTokenUpdate> {
    return useApi().post<UserTokenUpdate>('/users', data);
}

/**
 * Login with an identifier (email, or username when usernames are enabled).
 * Uses OAuth2 form format as expected by FastAPI.
 */
export async function login(identifier: string, password: string): Promise<UserTokenUpdate> {
    const basepath = useRuntimeConfig().public.apiBase;

    // FastAPI OAuth2 expects x-www-form-urlencoded; its "username" field carries
    // whatever identifier the user typed.
    const formData = new URLSearchParams();
    formData.append('username', identifier);
    formData.append('password', password);

    const response = await fetch(basepath + '/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw withStatus(new Error(error.detail || 'Invalid credentials'), response.status);
    }

    return response.json();
}

/**
 * Get current user info.
 */
export async function getCurrentUser(): Promise<UserRead> {
    return useApi().get<UserRead>('/users/me');
}

/**
 * Refresh auth token.
 */
export async function refreshToken(): Promise<UserTokenUpdate> {
    return useApi().put<UserTokenUpdate>('/users/me/token', {});
}

/**
 * Update user profile (first name, last name).
 */
export async function updateProfile(data: UserChangeInfo): Promise<UserRead> {
    return useApi().patch<UserRead>('/users/me', data);
}

/**
 * Change user password.
 */
export async function changePassword(data: UserChangePassword): Promise<UserRead> {
    return useApi().put<UserRead>('/users/me/password', data);
}

/**
 * Request email change. Sends confirmation email to the new address.
 */
export async function requestEmailChange(data: UserChangeEmail): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/users/me/email-changes', data);
}

/**
 * Request account deletion. Sends a confirmation email with a 1h-TTL link.
 */
export async function requestAccountDeletion(): Promise<AuthMessageResponse> {
    return useApi().post<AuthMessageResponse>('/users/me/account-deletions', {});
}
