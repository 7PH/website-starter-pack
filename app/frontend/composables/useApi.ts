// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

export interface ApiFetchOptions extends RequestInit {
    /** Number of retry attempts for failed requests (default: 0) */
    retries?: number;
    /** Base delay in ms between retries (default: 1000) */
    retryDelay?: number;
    /** Maximum delay between retries in ms (default: 10000) */
    maxRetryDelay?: number;
    /** HTTP status codes that should trigger a retry (default: [502, 503, 504]) */
    retryOn?: number[];
}

function getHeaders(options: RequestInit = {}): HeadersInit {
    const authStore = useAuth();
    return {
        'Content-Type': 'application/json',
        ...(authStore.isLoggedIn ? { Authorization: `Bearer ${authStore.token?.access_token}` } : {}),
        ...options.headers,
    };
}

/**
 * Sleep for a given number of milliseconds.
 */
function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Calculate exponential backoff delay with jitter.
 */
function getRetryDelay(attempt: number, baseDelay: number, maxDelay: number): number {
    const exponentialDelay = baseDelay * 2 ** attempt;
    const jitter = Math.random() * 0.3 * exponentialDelay; // Add up to 30% jitter
    return Math.min(exponentialDelay + jitter, maxDelay);
}

/**
 * Make an authenticated API request with optional retry logic.
 */
async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
    const authStore = useAuth();
    const config = useRuntimeConfig();
    // SSR uses the internal Docker hostname; browser uses the public relative path.
    const basepath = import.meta.server && config.apiInternal ? config.apiInternal : config.public.apiBase;

    const {
        retries = 0,
        retryDelay = 1000,
        maxRetryDelay = 10000,
        retryOn = [502, 503, 504],
        ...fetchOptions
    } = options;

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const response = await fetch(basepath + path, {
                ...fetchOptions,
                headers: getHeaders(fetchOptions),
            });

            if (!response.ok) {
                // Check if we should retry this status code
                if (retries > 0 && attempt < retries && retryOn.includes(response.status)) {
                    const delay = getRetryDelay(attempt, retryDelay, maxRetryDelay);
                    await sleep(delay);
                    continue;
                }

                if (response.headers.get('WWW-Authenticate')?.includes('invalid_token')) {
                    authStore.logout();
                    throw new Error('Invalid or expired token');
                }

                // For server errors (5xx), show generic message to avoid leaking internal details
                if (response.status >= 500) {
                    throw new Error('Server error. Please try again later.');
                }

                // For client errors (4xx), try to parse error detail
                let errorData: { detail?: string } = {};
                try {
                    errorData = await response.json();
                } catch {
                    throw withStatus(new Error(response.statusText ?? 'An error occurred'), response.status);
                }

                throw withStatus(
                    new Error(errorData.detail ?? response.statusText ?? 'An error occurred'),
                    response.status,
                );
            }

            // Only parse JSON if there's content
            const text = await response.text();
            return text ? JSON.parse(text) : (undefined as unknown as T);
        } catch (error) {
            lastError = error instanceof Error ? error : new Error(String(error));

            // Don't retry on AbortError (cancelled requests)
            if (lastError.name === 'AbortError') {
                throw lastError;
            }

            // Retry on network errors if we have retries left
            if (retries > 0 && attempt < retries) {
                const delay = getRetryDelay(attempt, retryDelay, maxRetryDelay);
                await sleep(delay);
                continue;
            }

            throw lastError;
        }
    }

    throw lastError || new Error('Request failed');
}

/**
 * Make an API request and show error toast on failure.
 */
async function apiFetchOrError<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
    try {
        return await apiFetch<T>(path, options);
    } catch (error) {
        // Don't show toast for aborted requests
        if (error instanceof Error && error.name === 'AbortError') {
            throw error;
        }

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
 * Create an AbortController for request cancellation.
 * Returns the controller and a cleanup function to call on component unmount.
 */
function createAbortController(): { controller: AbortController; cleanup: () => void } {
    const controller = new AbortController();
    const cleanup = () => controller.abort();
    return { controller, cleanup };
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
function withBody(method: string, body?: unknown, options?: ApiFetchOptions): ApiFetchOptions {
    return {
        method,
        body: body ? JSON.stringify(body) : undefined,
        ...options,
    };
}

/**
 * API composable with convenience methods for common HTTP verbs.
 * Auto-imported by Nuxt - use directly: `const api = useApi()`
 *
 * Features:
 * - Automatic auth token handling
 * - Optional retry with exponential backoff
 * - Request cancellation via AbortController
 *
 * @example
 * // Basic usage
 * const api = useApi()
 * const data = await api.get('/users')
 *
 * @example
 * // With retry
 * const data = await api.get('/users', {}, { retries: 3 })
 *
 * @example
 * // With cancellation
 * const { controller, cleanup } = api.createAbortController()
 * onUnmounted(cleanup)
 * const data = await api.get('/users', {}, { signal: controller.signal })
 */
export function useApi() {
    return {
        fetch: apiFetch,
        fetchOrError: apiFetchOrError,
        createAbortController,

        get<T>(path: string, params?: Record<string, unknown>, options?: ApiFetchOptions) {
            return apiFetch<T>(buildUrl(path, params), options);
        },

        post<T>(path: string, body?: unknown, options?: ApiFetchOptions) {
            return apiFetch<T>(path, withBody('POST', body, options));
        },

        put<T>(path: string, body: unknown, options?: ApiFetchOptions) {
            return apiFetch<T>(path, withBody('PUT', body, options));
        },

        patch<T>(path: string, body: unknown, options?: ApiFetchOptions) {
            return apiFetch<T>(path, withBody('PATCH', body, options));
        },

        delete<T>(path: string, options?: ApiFetchOptions) {
            return apiFetch<T>(path, { method: 'DELETE', ...options });
        },
    };
}
