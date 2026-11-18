/**
 * Project-specific admin navigation items.
 * Add your custom admin pages here. They show in the admin sidebar, in the "Project" group unless you set `group`
 * ('content', 'people', 'system', or any other string for a new group with that name).
 *
 * Example:
 * export const PROJECT_ADMIN_NAV: AdminNavItem[] = [
 *     { label: 'Orders', icon: 'i-lucide-shopping-cart', to: '/admin/orders', order: 15, group: 'Shop' },
 *     { label: 'Articles', icon: 'i-lucide-file-text', to: '/admin/articles', order: 25, group: 'content' },
 * ];
 *
 * An item with the same `to` as a core item replaces it, eg to relabel or regroup it. Add `condition: () => false` to
 * hide it (the page itself stays reachable):
 *     { label: 'Orgs', icon: 'i-lucide-building-2', to: '/admin/organizations', condition: () => false },
 */

import type { AdminNavItem } from './admin-nav';

export const PROJECT_ADMIN_NAV: AdminNavItem[] = [
    // Add your custom admin pages here
];
