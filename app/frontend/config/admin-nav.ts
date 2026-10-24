// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Admin navigation configuration.
 * Projects can extend by creating config/admin-nav-ext.ts with PROJECT_ADMIN_NAV.
 */

export interface AdminNavItem {
    /** Display label */
    label: string;
    /** i18n key, wins over label when set (for screens CMS editors use) */
    labelKey?: string;
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
    /** Also shown to CMS editors, who only see these items */
    editorAccess?: boolean;
}

/**
 * Core admin navigation items.
 * These are managed by the starterpack.
 */
export const CORE_ADMIN_NAV: AdminNavItem[] = [
    {
        label: 'Pages',
        labelKey: 'cms.nav.pages',
        icon: 'i-lucide-file-text',
        to: '/admin/cms/pages',
        order: 5,
        condition: isCmsEnabled,
        editorAccess: true,
    },
    {
        label: 'Photos',
        labelKey: 'cms.nav.media',
        icon: 'i-lucide-image',
        to: '/admin/cms/media',
        order: 6,
        condition: isCmsEnabled,
        editorAccess: true,
    },
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
        label: 'Orgs',
        icon: 'i-lucide-building-2',
        to: '/admin/organizations',
        order: 15,
        condition: () => useRuntimeConfig().public.organizationsEnabled === true,
    },
    {
        label: 'Events',
        icon: 'i-lucide-list',
        to: '/admin/events',
        order: 20,
    },
    {
        label: 'DB',
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
    {
        label: 'Config',
        icon: 'i-lucide-settings',
        to: '/admin/config',
        order: 35,
    },
];
