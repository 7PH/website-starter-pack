// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
//
// Security boundary for rendering user-generated markdown as HTML.
// Two layers of defense:
//   1. markdown-it with html:false and html_block/html_inline disabled — raw HTML
//      in the source is escaped, never parsed.
//   2. DOMPurify strict allowlist on the output — tags/attrs not in the list are
//      stripped. DOMPurify's default ALLOWED_URI_REGEXP blocks javascript:, data:,
//      vbscript: hrefs.
// Every <a> gets rel="noopener noreferrer nofollow" target="_blank" via a hook
// installed on a private DOMPurify instance, so the hook can't leak to other
// callers of the global DOMPurify singleton.
//
// SSR: DOMPurify silently returns its input unchanged when no DOM is available,
// which would fail-open. We refuse to render on the server so the sanitizer
// can never be bypassed by a misconfigured caller.

import createDOMPurify from 'dompurify';
import type { DOMPurify as DOMPurifyInstance } from 'dompurify';
import MarkdownIt from 'markdown-it';

const ALLOWED_TAGS = [
    'p',
    'br',
    'strong',
    'em',
    'code',
    'pre',
    'ul',
    'ol',
    'li',
    'blockquote',
    'a',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
];
const ALLOWED_ATTR = ['href', 'title', 'rel', 'target'];

let mdInstance: MarkdownIt | null = null;
let purifierInstance: DOMPurifyInstance | null = null;

function getMarkdownIt(): MarkdownIt {
    if (mdInstance) return mdInstance;
    const md = new MarkdownIt({
        html: false,
        linkify: true,
        breaks: true,
        typographer: false,
    });
    md.disable(['table', 'image', 'html_block', 'html_inline']);
    mdInstance = md;
    return md;
}

function getPurifier(): DOMPurifyInstance {
    if (purifierInstance) return purifierInstance;
    const purifier = createDOMPurify(window);
    purifier.addHook('afterSanitizeAttributes', (node) => {
        if (node.nodeName === 'A') {
            node.setAttribute('rel', 'noopener noreferrer nofollow');
            node.setAttribute('target', '_blank');
        }
    });
    purifierInstance = purifier;
    return purifier;
}

export function renderMarkdown(content: string): string {
    if (import.meta.server) return '';
    const html = getMarkdownIt().render(content ?? '');
    return getPurifier().sanitize(html, { ALLOWED_TAGS, ALLOWED_ATTR });
}
