// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { describe, expect, it } from 'vitest';
import { filterAdminNav, groupAdminNav, isAdminNavActive } from '~/utils/admin-nav';

const DEFS = {
    content: { label: 'Content', order: 10 },
    people: { label: 'People', order: 20 },
    project: { label: 'Project', order: 60 },
    system: { label: 'System', order: 80 },
    tools: { label: 'Tools', order: 90 },
};

const ITEMS = [
    { label: 'Config', group: 'system', order: 35 },
    { label: 'Users', group: 'people', order: 10 },
    { label: 'Invoices', group: 'Billing', order: 1 },
    { label: 'Flags' },
    { label: 'Events', group: 'system', order: 20 },
    { label: 'Adminer', group: 'system', external: true, order: 100 },
    { label: 'Coupons', group: 'Billing', order: 2 },
];

describe('groupAdminNav', () => {
    it('orders groups and items, puts ungrouped items in Project and external links in Tools', () => {
        const groups = groupAdminNav(ITEMS, DEFS);
        expect(groups.map((g) => [g.label, g.items.map((i) => i.label)])).toEqual([
            ['People', ['Users']],
            ['Billing', ['Invoices', 'Coupons']],
            ['Project', ['Flags']],
            ['System', ['Events', 'Config']],
            ['Tools', ['Adminer']],
        ]);
    });
});

describe('filterAdminNav', () => {
    const groups = groupAdminNav(ITEMS, DEFS);

    it('matches item labels, case-insensitive, and drops empty groups', () => {
        expect(filterAdminNav(groups, 'CON').map((g) => [g.label, g.items.map((i) => i.label)])).toEqual([
            ['System', ['Config']],
        ]);
    });

    it('keeps a whole group when its label matches', () => {
        expect(filterAdminNav(groups, 'system')[0]!.items).toHaveLength(2);
    });

    it('returns everything for a blank query', () => {
        expect(filterAdminNav(groups, '  ')).toBe(groups);
    });
});

describe('isAdminNavActive', () => {
    it.each([
        ['/admin/users', '/admin/users', true],
        ['/admin/users/5', '/admin/users', true],
        ['/admin/users-export', '/admin/users', false],
        ['/admin/users', undefined, false],
    ])('%s under %s -> %s', (path, to, expected) => {
        expect(isAdminNavActive(path, to)).toBe(expected);
    });
});
