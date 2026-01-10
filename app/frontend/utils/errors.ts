// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Extract error message from an unknown error.
 * Handles Error instances and falls back to a default message.
 */
export function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error) return error.message;
    return fallback;
}
