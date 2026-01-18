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
    /** Route path (for internal links) */
    to?: string;
    /** External URL (for external links) */
    href?: string;
    /** Whether this is an external link (opens in new tab) */
    external?: boolean;
    /** Sort order (lower = higher in list) */
    order?: number;
    /** Optional condition function - item hidden if returns false */
    condition?: () => boolean;
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
        label: 'Messages',
        icon: 'i-lucide-message-square',
        to: '/admin/messages',
        order: 12,
    },
    {
        label: 'Organizations',
        icon: 'i-lucide-building-2',
        to: '/admin/organizations',
        order: 15,
        condition: () => useRuntimeConfig().public.organizationsEnabled === true,
    },
    {
        label: 'Event Logs',
        icon: 'i-lucide-list',
        to: '/admin/events',
        order: 20,
    },
    {
        label: 'DB Health',
        icon: 'i-lucide-activity',
        to: '/admin/db-health',
        order: 25,
    },
    {
        label: 'Backups',
        icon: 'i-lucide-database-backup',
        to: '/admin/backups',
        order: 30,
    },
];
