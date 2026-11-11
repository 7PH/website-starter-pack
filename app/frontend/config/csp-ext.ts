/**
 * Extra Content-Security-Policy sources for this app, added to the core policy built in nuxt.config.ts.
 * Keys are directives, values the sources to allow. A directive the core doesn't set starts from 'self'.
 * Read at build time, so rebuild the frontend after changing it.
 *
 * @example YouTube embeds (components/common/YouTubeFacade.vue)
 * export const CSP_EXT: CspExt = {
 *     'frame-src': ['https://www.youtube-nocookie.com'],
 *     'img-src': ['https://i.ytimg.com'],
 * };
 */

export type CspExt = Partial<Record<string, string[]>>;

export const CSP_EXT: CspExt = {};
