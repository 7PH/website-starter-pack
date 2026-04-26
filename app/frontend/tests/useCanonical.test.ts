// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { describe, expect, it } from 'vitest';
import { buildCanonicalUrl } from '~/composables/useCanonical';

describe('buildCanonicalUrl', () => {
    it('joins relative path with base URL', () => {
        expect(buildCanonicalUrl('/about', 'https://example.com')).toBe('https://example.com/about');
    });

    it('strips trailing slash on base URL', () => {
        expect(buildCanonicalUrl('/about', 'https://example.com/')).toBe('https://example.com/about');
    });

    it('adds leading slash to path if missing', () => {
        expect(buildCanonicalUrl('about', 'https://example.com')).toBe('https://example.com/about');
    });

    it('returns absolute URLs unchanged', () => {
        expect(buildCanonicalUrl('https://other.com/page', 'https://example.com')).toBe('https://other.com/page');
        expect(buildCanonicalUrl('http://insecure.com/page', 'https://example.com')).toBe('http://insecure.com/page');
    });

    it('drops query string from relative paths', () => {
        expect(buildCanonicalUrl('/search?q=foo&page=2', 'https://example.com')).toBe('https://example.com/search');
    });

    it('preserves query string when path is an absolute URL', () => {
        expect(buildCanonicalUrl('https://other.com/x?q=1', 'https://example.com')).toBe('https://other.com/x?q=1');
    });

    it('handles root path', () => {
        expect(buildCanonicalUrl('/', 'https://example.com')).toBe('https://example.com/');
    });
});
