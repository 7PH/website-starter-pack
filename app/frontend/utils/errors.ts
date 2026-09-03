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
}

export function withStatus(error: Error, status: number): ApiError {
    (error as ApiError).status = status;
    return error;
}

export function getErrorStatus(error: unknown): number | undefined {
    return error instanceof Error ? (error as ApiError).status : undefined;
}
