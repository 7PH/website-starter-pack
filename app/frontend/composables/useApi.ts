// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

function getHeaders(options: RequestInit = {}): HeadersInit {
    const authStore = useAuth();
    return {
        'Content-Type': 'application/json',
        ...(authStore.isLoggedIn ? { Authorization: `Bearer ${authStore.token?.access_token}` } : {}),
        ...options.headers,
    };
}

/**
 * Make an authenticated API request.
 */
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const authStore = useAuth();
    const basepath = useRuntimeConfig().public.apiBase;

    const response = await fetch(basepath + path, {
        ...options,
        headers: getHeaders(options),
    });

    if (!response.ok) {
        if (response.headers.get('WWW-Authenticate')?.includes('invalid_token')) {
            authStore.logout();
            throw new Error('Invalid or expired token');
        }

        // For server errors (5xx), show generic message to avoid leaking internal details
        if (response.status >= 500) {
            throw new Error('Server error. Please try again later.');
        }

        // For client errors (4xx), try to parse error detail
        try {
            const errorData = await response.json();
            throw new Error(errorData.detail || response.statusText || 'An error occurred');
        } catch {
            throw new Error(response.statusText || 'An error occurred');
        }
    }

    return response.json();
}

/**
 * Make an API request and show error toast on failure.
 */
async function apiFetchOrError<T>(path: string, options: RequestInit = {}): Promise<T> {
    try {
        return await apiFetch<T>(path, options);
    } catch (error) {
        const toast = useToast();
        if (error instanceof Error) {
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: error.message,
                life: 5000,
            });
        }
        throw error;
    }
}

/**
 * API composable with convenience methods for common HTTP verbs.
 * Auto-imported by Nuxt - use directly: `const api = useApi()`
 */
export function useApi() {
    return {
        fetch: apiFetch,
        fetchOrError: apiFetchOrError,
        get: <T>(path: string, options?: RequestInit) => apiFetch<T>(path, options),
        post: <T>(path: string, body: unknown, options?: RequestInit) =>
            apiFetch<T>(path, { method: 'POST', body: JSON.stringify(body), ...options }),
        put: <T>(path: string, body: unknown, options?: RequestInit) =>
            apiFetch<T>(path, { method: 'PUT', body: JSON.stringify(body), ...options }),
        patch: <T>(path: string, body: unknown, options?: RequestInit) =>
            apiFetch<T>(path, { method: 'PATCH', body: JSON.stringify(body), ...options }),
        delete: <T>(path: string, options?: RequestInit) => apiFetch<T>(path, { method: 'DELETE', ...options }),
    };
}
