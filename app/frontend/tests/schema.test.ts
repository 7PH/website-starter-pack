// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

// Pure-builder coverage for the JSON-LD helpers in `~/composables/schema`.
// The `useSchema*` wrappers depend on Nuxt auto-imports (`useHead`) that
// vitest+jsdom doesn't provide, so the schema-emission behavior is exercised
// in e2e specs (sub-app responsibility for content pages).

import { describe, expect, it } from 'vitest';
import {
    buildArticleSchema,
    buildBreadcrumbListSchema,
    buildCourseSchema,
    buildFAQPageSchema,
    buildLdScript,
    buildLocalBusinessSchema,
    buildProductSchema,
    buildWebPageSchema,
} from '~/composables/schema';

describe('buildLdScript — script tag input', () => {
    it('returns valid JSON-LD script with correct type and key', () => {
        const out = buildLdScript('foo', { hello: 'world' });
        expect(out.type).toBe('application/ld+json');
        expect(out.key).toBe('ld-foo');
        expect(JSON.parse(out.innerHTML)).toEqual({ hello: 'world' });
    });

    it('escapes </ so user-supplied text cannot close the script tag', () => {
        const out = buildLdScript('foo', { name: "</script><script>alert('xss')</script>" });
        expect(out.innerHTML).not.toContain('</script>');
        expect(out.innerHTML).toContain('<\\/script>');
        // Still parseable after the escape.
        expect(() => JSON.parse(out.innerHTML)).not.toThrow();
    });
});

describe('buildCourseSchema', () => {
    it('produces a valid Course with provider Organization', () => {
        const out = buildCourseSchema({
            name: 'Music Theory 101',
            description: 'Read music in 4 weeks.',
            provider: 'Acme Music',
        });
        expect(out['@context']).toBe('https://schema.org');
        expect(out['@type']).toBe('Course');
        expect(out.name).toBe('Music Theory 101');
        expect(out.provider).toEqual({ '@type': 'Organization', name: 'Acme Music' });
        expect(out.isAccessibleForFree).toBe(true); // default
    });

    it('honors isAccessibleForFree=false', () => {
        const out = buildCourseSchema({ name: 'A', description: 'B', provider: 'C', isAccessibleForFree: false });
        expect(out.isAccessibleForFree).toBe(false);
    });
});

describe('buildFAQPageSchema', () => {
    it('maps items to Question/Answer structure', () => {
        const out = buildFAQPageSchema([
            { question: 'Q1?', answer: 'A1' },
            { question: 'Q2?', answer: 'A2' },
        ]);
        expect(out['@type']).toBe('FAQPage');
        expect(out.mainEntity).toHaveLength(2);
        expect(out.mainEntity[0]).toEqual({
            '@type': 'Question',
            name: 'Q1?',
            acceptedAnswer: { '@type': 'Answer', text: 'A1' },
        });
    });
});

describe('buildProductSchema', () => {
    it('coerces price to string per schema.org Offer', () => {
        const out = buildProductSchema({ name: 'Pro', offers: { price: 9.99, priceCurrency: 'EUR' } });
        expect(out['@type']).toBe('Product');
        expect(out.offers.price).toBe('9.99');
        expect(out.offers.priceCurrency).toBe('EUR');
    });
});

describe('buildLocalBusinessSchema', () => {
    it('emits LocalBusiness with optional geo', () => {
        const out = buildLocalBusinessSchema({
            name: 'Acme Music HQ',
            address: '1 rue de la Musique, Paris',
            geo: { latitude: 48.8566, longitude: 2.3522 },
        });
        expect(out['@type']).toBe('LocalBusiness');
        expect(out.geo).toEqual({ '@type': 'GeoCoordinates', latitude: 48.8566, longitude: 2.3522 });
    });

    it('omits geo when not provided', () => {
        const out = buildLocalBusinessSchema({ name: 'X', address: 'Y' });
        expect(out).not.toHaveProperty('geo');
    });

    it('emits a subtype with a postal address and drops missing fields', () => {
        const out = buildLocalBusinessSchema({
            type: 'HealthAndBeautyBusiness',
            name: 'Cabinet',
            telephone: '+33 1 23 45 67 89',
            address: {
                streetAddress: '1 rue Haute',
                postalCode: '75001',
                addressLocality: 'Paris',
                addressCountry: 'FR',
            },
            sameAs: ['https://maps.example.com/cabinet'],
        });
        expect(JSON.parse(buildLdScript('local-business', out).innerHTML)).toEqual({
            '@context': 'https://schema.org',
            '@type': 'HealthAndBeautyBusiness',
            name: 'Cabinet',
            telephone: '+33 1 23 45 67 89',
            sameAs: ['https://maps.example.com/cabinet'],
            address: {
                '@type': 'PostalAddress',
                streetAddress: '1 rue Haute',
                postalCode: '75001',
                addressLocality: 'Paris',
                addressCountry: 'FR',
            },
        });
    });
});

describe('buildWebPageSchema', () => {
    const page = { headline: 'Prices', url: 'https://example.com/prices', siteName: 'Site' };
    const site = { '@type': 'Organization', name: 'Site' };

    it('emits a WebPage by default, without the fields left out', () => {
        expect(JSON.parse(buildLdScript('page', buildWebPageSchema(page)).innerHTML)).toEqual({
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            headline: 'Prices',
            url: 'https://example.com/prices',
            author: site,
            publisher: site,
        });
    });

    it('emits an Article with its dates, image and main entity', () => {
        const out = buildWebPageSchema({
            ...page,
            type: 'Article',
            description: 'D',
            image: 'https://static.example.com/1.webp',
            datePublished: '2026-01-01T00:00:00Z',
            dateModified: '2026-02-01T00:00:00Z',
        });
        expect(out).toMatchObject({
            '@type': 'Article',
            description: 'D',
            image: 'https://static.example.com/1.webp',
            datePublished: '2026-01-01T00:00:00Z',
            dateModified: '2026-02-01T00:00:00Z',
            author: site,
            mainEntityOfPage: 'https://example.com/prices',
        });
    });
});

describe('buildBreadcrumbListSchema', () => {
    it('numbers items from 1 and uses absolute URLs as-is', () => {
        const out = buildBreadcrumbListSchema([
            { name: 'Home', item: 'https://example.com/' },
            { name: 'Theory', item: 'https://example.com/theory' },
        ]);
        expect(out['@type']).toBe('BreadcrumbList');
        expect(out.itemListElement).toEqual([
            { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://example.com/' },
            { '@type': 'ListItem', position: 2, name: 'Theory', item: 'https://example.com/theory' },
        ]);
    });
});

describe('buildArticleSchema', () => {
    it('emits a minimal Article with only @context + @type when no fields', () => {
        const out = buildArticleSchema({});
        expect(out).toEqual({ '@context': 'https://schema.org', '@type': 'Article' });
    });

    it('adds full article metadata when provided', () => {
        const out = buildArticleSchema({
            headline: 'My Post',
            author: 'Jane Doe',
            datePublished: '2026-01-15',
        });
        expect(out.headline).toBe('My Post');
        expect(out.author).toEqual({ '@type': 'Person', name: 'Jane Doe' });
        expect(out.datePublished).toBe('2026-01-15');
    });

    it('emits paywall fields for PremiumGate-style usage', () => {
        const out = buildArticleSchema({
            isAccessibleForFree: false,
            hasPart: { cssSelector: '#gate-1', isAccessibleForFree: false },
        });
        expect(out.isAccessibleForFree).toBe(false);
        expect(out.hasPart).toEqual([
            { '@type': 'WebPageElement', cssSelector: '#gate-1', isAccessibleForFree: false },
        ]);
    });

    it('accepts an array of hasPart entries', () => {
        const out = buildArticleSchema({
            hasPart: [{ cssSelector: '#section-1' }, { cssSelector: '#section-2', isAccessibleForFree: false }],
        });
        expect(out.hasPart).toHaveLength(2);
    });
});
