// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Format a date string for display (locale date only).
 */
export function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
}

/**
 * Format a date string for display with time (locale date and time).
 */
export function formatDateTime(dateStr: string | null | undefined): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
}

/**
 * Format a date string for time-only display (HH:MM).
 */
export function formatTime(dateStr: string | null | undefined): string {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Convert an event action like "user.login" into "User Login".
 */
export function formatAction(action: string): string {
    return action
        .split('.')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
}

/**
 * Build a display label for a user-preview shape (ConversationUserPreview):
 * first+last → email → ``fallback`` (default ``"Unknown"``).
 */
export function previewLabel(
    user: { first_name?: string | null; last_name?: string | null; email?: string | null } | null | undefined,
    fallback: string = 'Unknown',
): string {
    if (!user) return fallback;
    const name = [user.first_name, user.last_name].filter(Boolean).join(' ');
    return name || user.email || fallback;
}

/**
 * Format a billing interval for display.
 */
export function formatInterval(interval: string): string {
    const intervals: Record<string, string> = {
        month: '/mo',
        year: '/yr',
        week: '/wk',
        day: '/day',
    };
    return intervals[interval] || `/${interval}`;
}

/**
 * Format a price amount with currency.
 * Amount is expected to be in cents (smallest currency unit).
 */
export function formatPrice(amount: number, currency: string): string {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency.toUpperCase(),
    }).format(amount / 100);
}
