// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
//
// XSS + feature coverage for utils/markdown.ts. The sanitizer is a security
// boundary — any regression here ships an XSS. Payloads below cover the
// OWASP cheat-sheet classics plus a few markdown-specific tricks.

import { describe, expect, it } from 'vitest';
import { renderMarkdown } from '~/utils/markdown';

// Parse rendered HTML into a real DOM tree so we can assert on actual
// elements/attributes, not on text that happens to contain dangerous
// substrings (escaped payloads are safe even if they still read as
// `onerror=` inside a text node).
function parse(html: string): HTMLElement {
    const root = document.createElement('div');
    root.innerHTML = html;
    return root;
}

function allElements(root: HTMLElement): Element[] {
    return [root, ...Array.from(root.querySelectorAll('*'))];
}

describe('renderMarkdown — XSS defense', () => {
    it('escapes <script>', () => {
        const html = renderMarkdown("<script>alert('x')</script>");
        expect(html).not.toContain('<script');
        expect(html).toContain('&lt;script');
    });

    it('strips <img onerror>', () => {
        const html = renderMarkdown('<img src=x onerror=alert(1)>');
        const root = parse(html);
        expect(root.querySelector('img')).toBeNull();
        expect(allElements(root).some((el) => el.hasAttribute('onerror'))).toBe(false);
    });

    it('strips <iframe>', () => {
        const html = renderMarkdown('<iframe src="https://evil.com"></iframe>');
        expect(parse(html).querySelector('iframe')).toBeNull();
    });

    it('strips <svg onload>', () => {
        const html = renderMarkdown('<svg onload=alert(1)></svg>');
        const root = parse(html);
        expect(root.querySelector('svg')).toBeNull();
        expect(allElements(root).some((el) => el.hasAttribute('onload'))).toBe(false);
    });

    it('does not emit <a> for javascript: href', () => {
        const html = renderMarkdown('[click](javascript:alert(1))');
        expect(html).not.toMatch(/<a\b[^>]*href=/i);
    });

    it('does not emit <a> for data: href', () => {
        const html = renderMarkdown('[click](data:text/html,<script>alert(1)</script>)');
        expect(html).not.toMatch(/<a\b[^>]*href=/i);
        expect(html).not.toMatch(/<script/i);
    });

    it('does not emit <a> for vbscript: href', () => {
        const html = renderMarkdown('[click](vbscript:msgbox(1))');
        expect(html).not.toMatch(/<a\b[^>]*href=/i);
    });

    it('strips markdown images (feature disabled)', () => {
        const html = renderMarkdown('![alt](https://example.com/x.png)');
        expect(html).not.toMatch(/<img/i);
    });

    it('treats tables as plain text (feature disabled)', () => {
        const html = renderMarkdown('| a | b |\n|---|---|\n| 1 | 2 |');
        expect(html).not.toMatch(/<table/i);
    });

    it('strips inline style attributes', () => {
        const html = renderMarkdown('<p style="background:url(javascript:alert(1))">x</p>');
        const root = parse(html);
        expect(allElements(root).some((el) => el.hasAttribute('style'))).toBe(false);
    });
});

describe('renderMarkdown — link safety', () => {
    it('rewrites safe links with rel and target', () => {
        const html = renderMarkdown('[example](https://example.com)');
        expect(html).toMatch(/<a\b[^>]*href="https:\/\/example\.com"/);
        expect(html).toContain('rel="noopener noreferrer nofollow"');
        expect(html).toContain('target="_blank"');
    });

    it('auto-linked URLs also get rel and target', () => {
        const html = renderMarkdown('visit https://example.com for info');
        expect(html).toContain('href="https://example.com"');
        expect(html).toContain('rel="noopener noreferrer nofollow"');
        expect(html).toContain('target="_blank"');
    });

    it('allows mailto: links', () => {
        const html = renderMarkdown('[mail](mailto:a@b.com)');
        expect(html).toContain('href="mailto:a@b.com"');
    });
});

describe('renderMarkdown — allowed features', () => {
    it('renders headings h1–h6', () => {
        const html = renderMarkdown('# one\n## two\n### three\n#### four\n##### five\n###### six');
        expect(html).toMatch(/<h1>one<\/h1>/);
        expect(html).toMatch(/<h2>two<\/h2>/);
        expect(html).toMatch(/<h3>three<\/h3>/);
        expect(html).toMatch(/<h6>six<\/h6>/);
    });

    it('renders bold and italic', () => {
        const html = renderMarkdown('**bold** and *em*');
        expect(html).toContain('<strong>bold</strong>');
        expect(html).toContain('<em>em</em>');
    });

    it('renders inline code', () => {
        const html = renderMarkdown('use `x = 1`');
        expect(html).toContain('<code>x = 1</code>');
    });

    it('renders fenced code blocks', () => {
        const html = renderMarkdown('```\nhello\n```');
        expect(html).toMatch(/<pre><code>hello/);
    });

    it('renders bullet and ordered lists', () => {
        const html = renderMarkdown('- one\n- two\n\n1. a\n2. b');
        expect(html).toContain('<ul>');
        expect(html).toContain('<ol>');
        expect(html).toContain('<li>one</li>');
    });

    it('renders blockquotes', () => {
        const html = renderMarkdown('> quoted');
        expect(html).toMatch(/<blockquote>\s*<p>quoted<\/p>\s*<\/blockquote>/);
    });

    it('converts soft line breaks to <br>', () => {
        const html = renderMarkdown('line one\nline two');
        expect(html).toContain('<br>');
    });
});

describe('renderMarkdown — robustness', () => {
    it('handles empty input', () => {
        expect(renderMarkdown('')).toBe('');
    });

    it('handles 10k-char input without throwing', () => {
        const big = 'a '.repeat(5000);
        expect(() => renderMarkdown(big)).not.toThrow();
    });
});
