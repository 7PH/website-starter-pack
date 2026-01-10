// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Format a date string for display.
 */
export function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
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
