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
                color: 'error',
                title: 'Error',
                description: error.message,
                duration: 5000,
            });
        }
        throw error;
    }
}

/**
 * Build URL with query parameters.
 */
function buildUrl(path: string, params?: Record<string, unknown>): string {
    if (!params) return path;
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
            searchParams.append(key, String(value));
        }
    }
    const queryString = searchParams.toString();
    return queryString ? `${path}?${queryString}` : path;
}

/**
 * Helper to create request options with JSON body.
 */
function withBody(method: string, body?: unknown, options?: RequestInit): RequestInit {
    return {
        method,
        body: body ? JSON.stringify(body) : undefined,
        ...options,
    };
}

/**
 * API composable with convenience methods for common HTTP verbs.
 * Auto-imported by Nuxt - use directly: `const api = useApi()`
 */
export function useApi() {
    return {
        fetch: apiFetch,
        fetchOrError: apiFetchOrError,

        get<T>(path: string, params?: Record<string, unknown>, options?: RequestInit) {
            return apiFetch<T>(buildUrl(path, params), options);
        },

        post<T>(path: string, body?: unknown, options?: RequestInit) {
            return apiFetch<T>(path, withBody('POST', body, options));
        },

        put<T>(path: string, body: unknown, options?: RequestInit) {
            return apiFetch<T>(path, withBody('PUT', body, options));
        },

        patch<T>(path: string, body: unknown, options?: RequestInit) {
            return apiFetch<T>(path, withBody('PATCH', body, options));
        },

        delete<T>(path: string, options?: RequestInit) {
            return apiFetch<T>(path, { method: 'DELETE', ...options });
        },
    };
}
