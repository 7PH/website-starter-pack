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
 * Login with email and password.
 * Uses OAuth2 form format as expected by FastAPI.
 */
export async function login(email: string, password: string): Promise<UserTokenUpdate> {
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
