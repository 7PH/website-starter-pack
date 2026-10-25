// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import type { AdminNavItem } from '~/config/admin-nav';
import { ADMIN_NAV_GROUPS, CORE_ADMIN_NAV, useOpenConversationCount } from '~/config/admin-nav';
import { PROJECT_ADMIN_NAV } from '~/config/admin-nav-ext';
import { adminGetConversations } from '~/utils/api/conversations';

/** A nav item ready to render: label translated, badge evaluated. */
export type AdminNavLink = Omit<AdminNavItem, 'labelKey' | 'badge' | 'condition'> & { badge?: number };

/**
 * Admin sidebar groups (core + PROJECT_ADMIN_NAV + Adminer/Umami links), shared by the desktop sidebar and the mobile drawer.
 * `text(english, key)` gives the shell's own strings: English for admins, translated for CMS editors, whose admin is client-facing.
 *
 * @example
 * const { groups, text } = useAdminNav();
 */
export function useAdminNav() {
    const config = useRuntimeConfig();
    const { t } = useI18n();
    const { isEditorOnly } = useCmsAccess();

    function text(english: string, key: string, params?: Record<string, string>): string {
        return isEditorOnly.value ? t(key, params ?? {}) : english;
    }

    const groups = computed(() => {
        const items: AdminNavItem[] = [...CORE_ADMIN_NAV, ...PROJECT_ADMIN_NAV];
        if (config.public.adminerUrl) {
            items.push({
                label: 'Adminer',
                icon: 'i-lucide-database',
                href: config.public.adminerUrl as string,
                external: true,
                order: 100,
            });
        }
        if (config.public.umamiDashboardUrl) {
            items.push({
                label: 'Analytics',
                icon: 'i-lucide-bar-chart-3',
                href: config.public.umamiDashboardUrl as string,
                external: true,
                order: 101,
            });
        }
        const links = items
            .filter((item) => !item.condition || item.condition())
            // CMS editors reach admin pages without being admin: they only get the items flagged for them.
            .filter((item) => !isEditorOnly.value || item.editorAccess)
            .map(
                ({ labelKey, badge, condition: _condition, ...item }): AdminNavLink => ({
                    ...item,
                    label: labelKey ? text(item.label, labelKey) : item.label,
                    badge: badge?.(),
                }),
            );
        const defs = Object.fromEntries(
            Object.entries(ADMIN_NAV_GROUPS).map(([id, def]) => [
                id,
                { ...def, label: def.labelKey ? text(def.label, def.labelKey) : def.label },
            ]),
        );
        return groupAdminNav(links, defs);
    });

    return { groups, text };
}

/** Loads the core badge counts. Called once per admin layout mount; a failure just leaves the badge hidden. */
export async function loadAdminNavBadges(): Promise<void> {
    const openConversations = useOpenConversationCount();
    try {
        openConversations.value = (await adminGetConversations({ limit: 1 })).total;
    } catch {
        // No badge.
    }
}
