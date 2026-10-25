// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { describe, expect, it } from 'vitest';
import {
    autoSlug,
    cmsErrorKey,
    cmsLabel,
    hasReservedPrefix,
    inlineImageSrc,
    isEmptyField,
    isShadowedSlug,
    normalizeLink,
    slugify,
} from '~/utils/cms';
import { withStatus } from '~/utils/errors';

describe('slugify', () => {
    // Same cases as the backend (tests/test_cms_pages.py) so both sides agree.
    it.each([
        ["L'été à Paris", 'l-ete-a-paris'],
        ['Cœur & Âme', 'coeur-ame'],
        ['  Déjà vu !!  ', 'deja-vu'],
        ['Ça coûte 10 €', 'ca-coute-10'],
        ['???', ''],
        ['S’ancrer', 's-ancrer'],
        ['L’été', 'l-ete'],
        ['Aujourd‘hui ʼok´ `x`', 'aujourd-hui-ok-x'],
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
        }) as unknown as CmsMediaPublic;

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
        ['06 12 34 56 78', 'tel:0612345678'],
        ['06.12.34.56.78', 'tel:0612345678'],
        ['+33 6 12 34 56 78', 'tel:+33612345678'],
        ['tel:0612345678', 'tel:0612345678'],
        ['2024', 'https://2024'],
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

describe('isShadowedSlug', () => {
    const paths = ['/', '/login', '/legal/privacy', '/c/:token', '/:slug(.*)*'];

    it('flags the first segment of any site route', () => {
        expect(isShadowedSlug('login', paths)).toBe(true);
        expect(isShadowedSlug('legal', paths)).toBe(true);
        expect(isShadowedSlug('c', paths)).toBe(true);
    });

    it('ignores top-level params and other addresses', () => {
        expect(isShadowedSlug('accueil', paths)).toBe(false);
        expect(isShadowedSlug('privacy', paths)).toBe(false);
        expect(isShadowedSlug('', paths)).toBe(false);
    });
});

describe('isEmptyField', () => {
    const field = (type: CmsTemplateField['type']) => ({ type }) as CmsTemplateField;

    it('treats blank text, tag-only rich text and no photo as empty', () => {
        expect(isEmptyField(field('text'), '  ')).toBe(true);
        expect(isEmptyField(field('richtext'), '<p> </p>')).toBe(true);
        expect(isEmptyField(field('image'), null)).toBe(true);
        expect(isEmptyField(field('richtext'), '<p><img src="/a.webp"></p>')).toBe(false);
        expect(isEmptyField(field('text'), 'Bonjour')).toBe(false);
    });
});

describe('cmsErrorKey', () => {
    const error = (status: number, detail: string) => withStatus(new Error(detail), status);

    it.each([
        [409, 'slug_taken', 'cms.pages.slugTaken', undefined],
        [409, 'changed_elsewhere', 'cms.pages.changedElsewhere', undefined],
        [422, 'This address is reserved by the site', 'cms.pages.slugReserved', undefined],
        [422, 'Title is required', 'cms.pages.titleRequired', undefined],
        [422, "Field 'intro' is required", 'cms.pages.required', 'intro'],
        [422, "Field 'body' is too long", 'cms.pages.tooLong', 'body'],
        [422, "Field 'body' has too many photos", 'cms.pages.tooManyPhotos', 'body'],
        [422, '[object Object]', 'cms.errors.generic', undefined],
        [500, 'Server error. Please try again later.', 'cms.errors.generic', undefined],
    ])('%i %s -> %s', (status, detail, key, field) => {
        expect(cmsErrorKey(error(status, detail))).toEqual(field ? { key, field } : { key });
    });
});
