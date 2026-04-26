// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { buildCanonicalUrl } from '~/composables/useCanonical';
import { useSchemaBreadcrumbList } from '~/composables/schema';

/**
 * Breadcrumb building block: emits BreadcrumbList JSON-LD and decorates items
 * with a11y metadata. Use this from any breadcrumb visual (the default
 * `<Breadcrumb>` component does, and any sub-app override should call it
 * first thing in setup so SEO stays correct).
 *
 * @example
 * const { items } = useBreadcrumb([
 *     { label: 'Learn', to: '/app' },
 *     { label: 'Music theory', to: '/app/theory' },
 *     { label: 'Note reading' },
 * ]);
 */

export interface BreadcrumbInputItem {
    /** Visible label. */
    label: string;
    /** Path or absolute URL. Omit for the current page (typically the last item). */
    to?: string;
}

export interface BreadcrumbDecoratedItem extends BreadcrumbInputItem {
    isLast: boolean;
    ariaCurrent: 'page' | undefined;
}

export function useBreadcrumb(items: BreadcrumbInputItem[]) {
    const baseUrl = useRuntimeConfig().public.baseUrl;
    const decorated = buildBreadcrumbItems(items);

    // Schema needs absolute URLs. Items without `to` are skipped (the current
    // page typically has no link).
    const schemaItems = items
        .filter((item): item is Required<BreadcrumbInputItem> => item.to !== undefined)
        .map((item) => ({
            name: item.label,
            item: buildCanonicalUrl(item.to, baseUrl),
        }));

    if (schemaItems.length > 0) {
        useSchemaBreadcrumbList(schemaItems);
    }

    return { items: decorated };
}

/**
 * Pure decorator: marks the last item, sets `aria-current="page"` on it.
 */
export function buildBreadcrumbItems(items: BreadcrumbInputItem[]): BreadcrumbDecoratedItem[] {
    return items.map((item, index) => {
        const isLast = index === items.length - 1;
        return {
            ...item,
            isLast,
            ariaCurrent: isLast ? 'page' : undefined,
        };
    });
}
