// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { describe, expect, it } from 'vitest';
import { autoSlug, cmsLabel, hasReservedPrefix, inlineImageSrc, normalizeLink, slugify } from '~/utils/cms';

describe('slugify', () => {
    // Same cases as the backend (tests/test_cms_pages.py) so both sides agree.
    it.each([
        ["L'été à Paris", 'l-ete-a-paris'],
        ['Cœur & Âme', 'coeur-ame'],
        ['  Déjà vu !!  ', 'deja-vu'],
        ['Ça coûte 10 €', 'ca-coute-10'],
        ['???', ''],
    ])('%s -> %s', (title, slug) => {
        expect(slugify(title)).toBe(slug);
    });
});

describe('cmsLabel', () => {
    it('falls back to English, then any locale', () => {
        expect(cmsLabel({ en: 'Home', fr: 'Accueil' }, 'fr')).toBe('Accueil');
        expect(cmsLabel({ en: 'Home' }, 'fr')).toBe('Home');
        expect(cmsLabel({ de: 'Start' }, 'fr')).toBe('Start');
        expect(cmsLabel({}, 'fr')).toBe('');
    });
});

describe('inlineImageSrc', () => {
    const media = (widths: number[]) =>
        ({
            urls: Object.fromEntries(widths.map((w) => [String(w), `/${w}.webp`])),
            src: `/${Math.max(...widths)}.webp`,
        }) as unknown as CmsMediaRead;

    it('picks the largest width up to 1600', () => {
        expect(inlineImageSrc(media([480, 960, 1600, 2400]))).toBe('/1600.webp');
    });

    it('falls back to src when every width is larger', () => {
        expect(inlineImageSrc(media([2400]))).toBe('/2400.webp');
    });
});

describe('normalizeLink', () => {
    it.each([
        ['www.mairie.fr', 'https://www.mairie.fr'],
        ['  example.com/page ', 'https://example.com/page'],
        ['contact@example.com', 'mailto:contact@example.com'],
        ['https://example.com', 'https://example.com'],
        ['mailto:a@b.fr', 'mailto:a@b.fr'],
        ['/contact', '/contact'],
        ['#top', '#top'],
        ['', ''],
    ])('%s -> %s', (input, href) => {
        expect(normalizeLink(input)).toBe(href);
    });
});

describe('autoSlug', () => {
    it('keeps short titles whole and cuts long ones between words', () => {
        expect(autoSlug('À propos')).toBe('a-propos');
        const title = 'Un titre vraiment très long '.repeat(7);
        const slug = autoSlug(title);
        expect(slug.length).toBeLessThanOrEqual(80);
        expect(slugify(title).startsWith(`${slug}-`)).toBe(true);
    });
});

describe('hasReservedPrefix', () => {
    it('flags addresses routed to the backend or blocked by robots.txt', () => {
        expect(hasReservedPrefix('apiculture')).toBe(true);
        expect(hasReservedPrefix('administration-du-cabinet')).toBe(true);
        expect(hasReservedPrefix('accueil')).toBe(false);
    });
});
