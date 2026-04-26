/**
 * Sub-app extension for /robots.txt.
 *
 * Return additional Disallow paths to append to the dynamic robots.txt. The
 * starterpack already ships defaults: Disallow /admin, /api. Add per-app
 * private paths here.
 *
 * @example
 * export default async function (): Promise<string[]> {
 *     return ['/preview', '/internal'];
 * }
 */
export default async function (): Promise<string[]> {
    return [];
}
