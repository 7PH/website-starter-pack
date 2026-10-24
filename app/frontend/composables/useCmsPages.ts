// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { getErrorStatus } from '~/utils/errors';

/** Fetch during SSR; a 404 resolves to null instead of an error so pages can show their own not-found. */
function useCmsFetch<T>(key: string, path: string, params?: Record<string, unknown>) {
    const api = useApi();
    return useAsyncData<T | null>(key, async () => {
        try {
            return await api.get<T>(path, params);
        } catch (error) {
            if (getErrorStatus(error) === 404) return null;
            throw error;
        }
    });
}

/** A published free page by its address, or null. */
export function useCmsPage(slug: string) {
    return useCmsFetch<CmsPageRead>(`cms-page-${slug}`, `/cms/pages/by-slug/${encodeURIComponent(slug)}`);
}

/** A fixed page (home, site settings...) with its template defaults filled in. */
export function useCmsFixed(key: string) {
    return useCmsFetch<CmsPageRead>(`cms-fixed-${key}`, `/cms/fixed/${encodeURIComponent(key)}`);
}

/** Published pages marked "show in blog", newest first. */
export function useCmsPosts(options: { offset?: number; limit?: number } = {}) {
    const { offset = 0, limit = 10 } = options;
    return useCmsFetch<CmsPostListResponse>(`cms-posts-${offset}-${limit}`, '/cms/posts', { offset, limit });
}

/** Published pages of one template (eg every service), in the order the editor set. */
export function useCmsPageList(template: string, options: { offset?: number; limit?: number } = {}) {
    const { offset = 0, limit = 50 } = options;
    return useCmsFetch<CmsPageListResponse>(`cms-pages-${template}-${offset}-${limit}`, '/cms/pages', {
        template,
        offset,
        limit,
    });
}
