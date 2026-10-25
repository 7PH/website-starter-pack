// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

// Pure sidebar logic, kept apart from config/admin-nav.ts so it runs in unit tests without Nuxt.
import type { AdminNavGroupDef } from '~/config/admin-nav';

interface GroupableItem {
    label: string;
    group?: string;
    external?: boolean;
    order?: number;
}

export interface AdminNavGroup<T extends GroupableItem> {
    id: string;
    label: string;
    items: T[];
}

/** Sorts items by order into groups sorted by group order. No group: 'project'; external links: 'tools'; unknown ids: a group at order 50 named after the id. */
export function groupAdminNav<T extends GroupableItem>(
    items: T[],
    defs: Record<string, AdminNavGroupDef>,
): AdminNavGroup<T>[] {
    const groups = new Map<string, AdminNavGroup<T> & { order: number }>();
    for (const item of [...items].sort((a, b) => (a.order ?? 100) - (b.order ?? 100))) {
        const id = item.external ? 'tools' : (item.group ?? 'project');
        let group = groups.get(id);
        if (!group) {
            const def = defs[id] ?? { label: id, order: 50 };
            group = { id, label: def.label, order: def.order, items: [] };
            groups.set(id, group);
        }
        group.items.push(item);
    }
    return [...groups.values()].sort((a, b) => a.order - b.order).map(({ id, label, items }) => ({ id, label, items }));
}

/** Keeps items whose label or group label contains the query (case-insensitive), so "system" shows the whole group. */
export function filterAdminNav<T extends GroupableItem>(groups: AdminNavGroup<T>[], query: string): AdminNavGroup<T>[] {
    const q = query.trim().toLowerCase();
    if (!q) return groups;
    return groups
        .map((g) => ({
            ...g,
            items: g.label.toLowerCase().includes(q)
                ? g.items
                : g.items.filter((i) => i.label.toLowerCase().includes(q)),
        }))
        .filter((g) => g.items.length);
}

/** Whether `path` is the item's page or below it (`/admin/users/5` is under Users, `/admin/users-export` is not). */
export function isAdminNavActive(path: string, to: string | undefined): boolean {
    return !!to && (path === to || path.startsWith(`${to}/`));
}
