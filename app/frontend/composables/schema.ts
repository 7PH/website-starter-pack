// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Schema.org JSON-LD helpers.
 *
 * Each `useSchema*` helper emits a single `<script type="application/ld+json">`
 * via `useHead`. Pure builder functions are exported alongside (e.g.,
 * `buildCourseSchema`) so unit tests can assert on shape without needing a
 * Nuxt environment.
 *
 * `</` is escaped to `<\/` so a user-supplied string containing `</script>`
 * can't break out of the script tag (XSS defense for inline JSON-LD).
 *
 * Keys are scoped per schema type (`ld-course`, `ld-faq`, etc.) so multiple
 * helpers can run on the same page without colliding. If a page emits TWO of
 * the same type (e.g., two FAQ blocks), the later call replaces the earlier
 * via @unhead's key-based dedup.
 */

type LdScriptInput = {
    type: 'application/ld+json';
    innerHTML: string;
    key: string;
};

/**
 * Stringify a JSON-LD payload and escape `</` so a user-supplied string can't
 * break out of the surrounding `<script>` tag.
 */
export function buildLdScript(schemaType: string, payload: object): LdScriptInput {
    return {
        type: 'application/ld+json',
        innerHTML: JSON.stringify(payload).replaceAll('</', '<\\/'),
        key: `ld-${schemaType}`,
    };
}

// ─────────────────────────────────────────────────────────────────────────────
// Course
// ─────────────────────────────────────────────────────────────────────────────

export interface CourseInput {
    name: string;
    description: string;
    provider: string;
    isAccessibleForFree?: boolean;
}

export function buildCourseSchema(input: CourseInput) {
    return {
        '@context': 'https://schema.org',
        '@type': 'Course',
        name: input.name,
        description: input.description,
        provider: { '@type': 'Organization', name: input.provider },
        isAccessibleForFree: input.isAccessibleForFree ?? true,
    };
}

export function useSchemaCourse(input: CourseInput) {
    useHead({ script: [buildLdScript('course', buildCourseSchema(input))] });
}

// ─────────────────────────────────────────────────────────────────────────────
// FAQPage
// ─────────────────────────────────────────────────────────────────────────────

export interface FAQItem {
    question: string;
    answer: string;
}

export function buildFAQPageSchema(items: FAQItem[]) {
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: items.map((item) => ({
            '@type': 'Question',
            name: item.question,
            acceptedAnswer: { '@type': 'Answer', text: item.answer },
        })),
    };
}

export function useSchemaFAQPage(items: FAQItem[]) {
    useHead({ script: [buildLdScript('faq', buildFAQPageSchema(items))] });
}

// ─────────────────────────────────────────────────────────────────────────────
// Product
// ─────────────────────────────────────────────────────────────────────────────

export interface ProductInput {
    name: string;
    description?: string;
    offers: {
        price: number | string;
        priceCurrency: string;
    };
}

export function buildProductSchema(input: ProductInput) {
    return {
        '@context': 'https://schema.org',
        '@type': 'Product',
        name: input.name,
        ...(input.description && { description: input.description }),
        offers: {
            '@type': 'Offer',
            price: String(input.offers.price),
            priceCurrency: input.offers.priceCurrency,
        },
    };
}

export function useSchemaProduct(input: ProductInput) {
    useHead({ script: [buildLdScript('product', buildProductSchema(input))] });
}

// ─────────────────────────────────────────────────────────────────────────────
// LocalBusiness
// ─────────────────────────────────────────────────────────────────────────────

export interface LocalBusinessInput {
    name: string;
    address: string;
    geo?: { latitude: number; longitude: number };
}

export function buildLocalBusinessSchema(input: LocalBusinessInput) {
    return {
        '@context': 'https://schema.org',
        '@type': 'LocalBusiness',
        name: input.name,
        address: input.address,
        ...(input.geo && {
            geo: {
                '@type': 'GeoCoordinates',
                latitude: input.geo.latitude,
                longitude: input.geo.longitude,
            },
        }),
    };
}

export function useSchemaLocalBusiness(input: LocalBusinessInput) {
    useHead({ script: [buildLdScript('local-business', buildLocalBusinessSchema(input))] });
}

// ─────────────────────────────────────────────────────────────────────────────
// BreadcrumbList — caller passes already-resolved absolute URLs
// ─────────────────────────────────────────────────────────────────────────────

export interface BreadcrumbListItem {
    name: string;
    item: string;
}

export function buildBreadcrumbListSchema(items: BreadcrumbListItem[]) {
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        itemListElement: items.map((item, index) => ({
            '@type': 'ListItem',
            position: index + 1,
            name: item.name,
            item: item.item,
        })),
    };
}

export function useSchemaBreadcrumbList(items: BreadcrumbListItem[]) {
    useHead({ script: [buildLdScript('breadcrumb', buildBreadcrumbListSchema(items))] });
}

// ─────────────────────────────────────────────────────────────────────────────
// Article — all fields optional. Used by <PremiumGate> for paywall-only
// emission (isAccessibleForFree + hasPart) as well as by content pages for
// full article metadata.
// ─────────────────────────────────────────────────────────────────────────────

export interface ArticleHasPart {
    '@type'?: string;
    cssSelector: string;
    isAccessibleForFree?: boolean;
}

export interface ArticleInput {
    headline?: string;
    author?: string;
    datePublished?: string;
    isAccessibleForFree?: boolean;
    hasPart?: ArticleHasPart | ArticleHasPart[];
}

export function buildArticleSchema(input: ArticleInput) {
    const payload: Record<string, unknown> = {
        '@context': 'https://schema.org',
        '@type': 'Article',
    };
    if (input.headline !== undefined) payload.headline = input.headline;
    if (input.author !== undefined) {
        payload.author = { '@type': 'Person', name: input.author };
    }
    if (input.datePublished !== undefined) payload.datePublished = input.datePublished;
    if (input.isAccessibleForFree !== undefined) payload.isAccessibleForFree = input.isAccessibleForFree;
    if (input.hasPart !== undefined) {
        const parts = Array.isArray(input.hasPart) ? input.hasPart : [input.hasPart];
        payload.hasPart = parts.map((p) => ({
            '@type': p['@type'] ?? 'WebPageElement',
            cssSelector: p.cssSelector,
            ...(p.isAccessibleForFree !== undefined && { isAccessibleForFree: p.isAccessibleForFree }),
        }));
    }
    return payload;
}

export function useSchemaArticle(input: ArticleInput) {
    useHead({ script: [buildLdScript('article', buildArticleSchema(input))] });
}
