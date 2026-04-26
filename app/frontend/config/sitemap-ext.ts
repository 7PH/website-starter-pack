import type { SitemapUrlInput } from '@nuxtjs/sitemap';

/**
 * Sub-app extension for the sitemap.
 *
 * Return additional URLs to include in /sitemap.xml. The starterpack already
 * ships defaults for `/` and `/legal/*`. Use this for app-specific routes —
 * typically pages backed by your CMS or DB content.
 *
 * @example
 * export default async function (): Promise<SitemapUrlInput[]> {
 *     const courses = await fetchPublishedCourses();
 *     return courses.map((c) => ({
 *         loc: `/courses/${c.slug}`,
 *         lastmod: c.updatedAt,
 *         priority: 0.7,
 *     }));
 * }
 */
export default async function (): Promise<SitemapUrlInput[]> {
    return [];
}
