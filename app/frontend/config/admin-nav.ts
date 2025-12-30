// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Admin navigation configuration.
 * Projects can extend by creating config/admin-nav-ext.ts with PROJECT_ADMIN_NAV.
 */

export interface AdminNavItem {
    /** Display label */
    label: string;
    /** Icon name (e.g., 'i-lucide-users') */
    icon: string;
    /** Route path */
    to: string;
    /** Sort order (lower = higher in list) */
    order?: number;
}

/**
 * Core admin navigation items.
 * These are managed by the starterpack.
 */
export const CORE_ADMIN_NAV: AdminNavItem[] = [
    {
        label: 'Users',
        icon: 'i-lucide-users',
        to: '/admin/users',
        order: 10,
    },
    {
        label: 'Event Logs',
        icon: 'i-lucide-list',
        to: '/admin/events',
        order: 20,
    },
];
