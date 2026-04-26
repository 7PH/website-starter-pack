// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { describe, expect, it } from 'vitest';
import { buildBreadcrumbItems } from '~/composables/useBreadcrumb';

describe('buildBreadcrumbItems', () => {
    it('marks the last item as current and adds aria-current', () => {
        const [first, second, third] = buildBreadcrumbItems([
            { label: 'Home', to: '/' },
            { label: 'Articles', to: '/articles' },
            { label: 'Current page' },
        ]);
        expect(first?.isLast).toBe(false);
        expect(first?.ariaCurrent).toBeUndefined();
        expect(second?.isLast).toBe(false);
        expect(third?.isLast).toBe(true);
        expect(third?.ariaCurrent).toBe('page');
    });

    it('preserves label and to fields verbatim', () => {
        const [first, second] = buildBreadcrumbItems([{ label: 'Foo', to: '/foo' }, { label: 'Bar' }]);
        expect(first?.label).toBe('Foo');
        expect(first?.to).toBe('/foo');
        expect(second?.label).toBe('Bar');
        expect(second?.to).toBeUndefined();
    });

    it('handles a single-item list', () => {
        const [only] = buildBreadcrumbItems([{ label: 'Only' }]);
        expect(only?.isLast).toBe(true);
        expect(only?.ariaCurrent).toBe('page');
    });

    it('returns an empty array for empty input', () => {
        expect(buildBreadcrumbItems([])).toEqual([]);
    });
});
