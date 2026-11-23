// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Extract error message from an unknown error.
 * Handles Error instances and falls back to a default message.
 */
export function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error) return error.message;
    return fallback;
}

/** Error carrying the HTTP status that produced it, so callers can map a code to a message. */
export interface ApiError extends Error {
    status?: number;
    /** Seconds from a 429's Retry-After header. */
    retryAfter?: number;
}

export function withStatus(error: Error, status: number): ApiError {
    (error as ApiError).status = status;
    return error;
}

export function getErrorStatus(error: unknown): number | undefined {
    return error instanceof Error ? (error as ApiError).status : undefined;
}

/** Error for a failed response: its status, plus the wait a 429's Retry-After asks for. */
export function responseError(message: string, response: Response): ApiError {
    const error = withStatus(new Error(message), response.status);
    const retryAfter = Number(response.headers.get('Retry-After'));
    if (retryAfter > 0) error.retryAfter = retryAfter;
    return error;
}

export function getRetryAfter(error: unknown): number | undefined {
    return error instanceof Error ? (error as ApiError).retryAfter : undefined;
}

/** How long to wait, readable: "12 min", or "3 h" past two hours (daily caps). */
export function formatWait(seconds: number): string {
    const minutes = Math.ceil(seconds / 60);
    return minutes < 120 ? `${minutes} min` : `${Math.ceil(minutes / 60)} h`;
}
