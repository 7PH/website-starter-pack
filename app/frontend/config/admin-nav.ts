// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Admin navigation configuration.
 * Projects can extend by creating config/admin-nav-ext.ts with PROJECT_ADMIN_NAV.
 */

export interface AdminNavItem {
    /** Display label */
    label: string;
    /** i18n key shown to CMS editors instead of label (admins see label, the admin stays English for them) */
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
    /** Sidebar group: a key of ADMIN_NAV_GROUPS, or any other string for a new group with that label. Omitted: 'project'. External links always go to 'tools'. */
    group?: string;
    /** Count shown as a pill (a dot on the collapsed rail). A function so it can be reactive. Hidden when 0 or undefined. */
    badge?: () => number | undefined;
    /** Badge color (default 'primary') */
    badgeTone?: 'primary' | 'error';
}

export interface AdminNavGroupDef {
    label: string;
    /** i18n key shown to CMS editors instead of label */
    labelKey?: string;
    order: number;
}

/** Sidebar groups, by order. Groups not listed here sit at order 50, in the order they first appear. */
export const ADMIN_NAV_GROUPS: Record<string, AdminNavGroupDef> = {
    content: { label: 'Content', labelKey: 'cms.nav.content', order: 10 },
    people: { label: 'People', order: 20 },
    project: { label: 'Project', order: 60 },
    system: { label: 'System', order: 80 },
    tools: { label: 'Tools', order: 90 },
};

/** Open support conversations, loaded by the admin layout for the Messages badge. */
export const useOpenConversationCount = () => useState<number | undefined>('admin-open-conversations');

/**
 * Core admin navigation items.
 * These are managed by the starterpack.
 */
export const CORE_ADMIN_NAV: AdminNavItem[] = [
    {
        label: 'Pages',
        labelKey: 'cms.nav.pages',
        icon: 'i-lucide-file-text',
        group: 'content',
        to: '/admin/cms/pages',
        order: 5,
        condition: isCmsEnabled,
        editorAccess: true,
    },
    {
        label: 'Photos',
        labelKey: 'cms.nav.media',
        icon: 'i-lucide-image',
        group: 'content',
        to: '/admin/cms/media',
        order: 6,
        condition: isCmsEnabled,
        editorAccess: true,
    },
    {
        label: 'Users',
        icon: 'i-lucide-users',
        group: 'people',
        to: '/admin/users',
        order: 10,
    },
    {
        label: 'Messages',
        icon: 'i-lucide-message-square',
        group: 'people',
        to: '/admin/messages',
        order: 17,
        badge: () => useOpenConversationCount().value,
    },
    {
        label: 'Orgs',
        icon: 'i-lucide-building-2',
        group: 'people',
        to: '/admin/organizations',
        order: 15,
        condition: () => useRuntimeConfig().public.organizationsEnabled === true,
    },
    {
        label: 'Events',
        icon: 'i-lucide-list',
        group: 'system',
        to: '/admin/events',
        order: 20,
    },
    {
        label: 'DB health',
        icon: 'i-lucide-activity',
        group: 'system',
        to: '/admin/db-health',
        order: 25,
    },
    {
        label: 'Backups',
        icon: 'i-lucide-database-backup',
        group: 'system',
        to: '/admin/backups',
        order: 30,
    },
    {
        label: 'Config',
        icon: 'i-lucide-settings',
        group: 'system',
        to: '/admin/config',
        order: 35,
    },
];
