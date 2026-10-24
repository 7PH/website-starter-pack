// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/** Same rules as the backend's slugify (helpers/cms_pages.py), so the address preview matches what gets saved. */
export function slugify(value: string): string {
    return value
        .toLowerCase()
        .replace(/œ/g, 'oe')
        .replace(/æ/g, 'ae')
        .replace(/ß/g, 'ss')
        .normalize('NFKD')
        .replace(/[^\x00-\x7f]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .slice(0, 200)
        .replace(/^-+|-+$/g, '');
}

/** /api* goes to the backend and robots.txt blocks /api* and /admin*. Other site routes are caught with the router. */
const RESERVED_SLUG_PREFIXES = ['api', 'admin'];

export function hasReservedPrefix(slug: string): boolean {
    return RESERVED_SLUG_PREFIXES.some((prefix) => slug.startsWith(prefix));
}

/** Slug made from a title, like the backend's auto_slug: at most 80 characters, cut between words. */
export function autoSlug(title: string): string {
    const slug = slugify(title);
    if (slug.length <= 80) return slug;
    const cut = slug.slice(0, 81);
    return cut.includes('-') ? cut.slice(0, cut.lastIndexOf('-')) : slug.slice(0, 80);
}

/** Pick a template label or help text: current locale, else English, else any. */
export function cmsLabel(texts: Record<string, string> | undefined, locale: string): string {
    if (!texts) return '';
    return texts[locale] ?? texts.en ?? Object.values(texts)[0] ?? '';
}

/** Typed links without a scheme ("www.mairie.fr") would become relative and 404: make them absolute, or mailto for an email. */
export function normalizeLink(value: string): string {
    const href = value.trim();
    if (!href || /^([a-z][a-z0-9+.-]*:|\/|#)/i.test(href)) return href;
    return /^[^\s/@]+@[^\s/@]+\.[^\s/@]+$/.test(href) ? `mailto:${href}` : `https://${href}`;
}

/** localStorage key holding the editor's unsaved changes, read by the preview tab. */
export function cmsDraftKey(pageId: number): string {
    return `cms-draft-${pageId}`;
}

/** Largest generated width up to 1600px: enough for a photo inside text, lighter than the original. */
export function inlineImageSrc(media: CmsMediaRead): string {
    const widths = Object.keys(media.urls)
        .map(Number)
        .filter((w) => w <= 1600);
    return widths.length ? media.urls[String(Math.max(...widths))]! : media.src;
}

/** Readable typography for rich text, shared by the public renderer and the editor. Colors are inherited, so it fits any site palette and dark mode. */
export const RICH_TEXT_CLASS = [
    'leading-relaxed break-words',
    '[&_h2]:text-2xl [&_h2]:font-semibold [&_h2]:mt-8 [&_h2]:mb-3',
    '[&_h3]:text-xl [&_h3]:font-semibold [&_h3]:mt-6 [&_h3]:mb-2',
    '[&_p]:my-4 [&_ul]:my-4 [&_ul]:list-disc [&_ul]:pl-6 [&_ol]:my-4 [&_ol]:list-decimal [&_ol]:pl-6 [&_li]:my-1',
    '[&_blockquote]:my-6 [&_blockquote]:border-l-4 [&_blockquote]:border-gray-300 [&_blockquote]:pl-4 [&_blockquote]:italic',
    '[&_a]:underline [&_a]:underline-offset-2',
    '[&_img]:my-6 [&_img]:max-w-full [&_img]:h-auto [&_img]:rounded-lg',
].join(' ');
