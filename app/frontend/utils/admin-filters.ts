// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Shared filter primitives for admin list pages (users, organizations, ...).
 * Keep them here so adding a new admin list doesn't fork yet another copy of
 * the same Yes/No/All select options.
 */

export const YES_NO_FILTER_OPTIONS = [
    { label: 'All', value: 'all' },
    { label: 'Yes', value: 'yes' },
    { label: 'No', value: 'no' },
];

export const DELETED_FILTER_OPTIONS = [
    { label: 'Hide deleted', value: 'hide' },
    { label: 'Show all', value: 'all' },
    { label: 'Only deleted', value: 'only' },
];

export function yesNoToBool(value: string): boolean | undefined {
    if (value === 'yes') return true;
    if (value === 'no') return false;
    return undefined;
}
