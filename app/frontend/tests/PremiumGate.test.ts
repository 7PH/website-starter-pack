// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

// Behavior coverage (slot rendering, hidden/aria-hidden/inert toggling, SSR
// emission of the gated section) lives in the Playwright e2e spec —
// `e2e/premium-gate.spec.ts` — because PremiumGate depends on Nuxt
// auto-imports (useId, useHead, useI18n, usePremiumStatus) that aren't
// available in the plain vitest+jsdom environment.
//
// The piece worth unit-testing in isolation is the JSON-LD escape rule:
// if a slot ever contains user-supplied text that includes `</script>`,
// the inline JSON-LD must escape it or the page breaks (and could become
// an XSS vector). The function below mirrors the one in PremiumGate.vue.
// If the shape changes, both must move together.

import { describe, expect, it } from 'vitest';

function buildJsonLd(gatedId: string): string {
    const payload = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        isAccessibleForFree: false,
        hasPart: {
            '@type': 'WebPageElement',
            isAccessibleForFree: false,
            cssSelector: `#${gatedId}`,
        },
    };
    return JSON.stringify(payload).replaceAll('</', '<\\/');
}

describe('PremiumGate JSON-LD', () => {
    it('declares the page as paywalled with a hasPart pointing at the gated id', () => {
        const out = buildJsonLd('gate-abc');
        const parsed = JSON.parse(out);
        expect(parsed.isAccessibleForFree).toBe(false);
        expect(parsed.hasPart).toMatchObject({
            '@type': 'WebPageElement',
            isAccessibleForFree: false,
            cssSelector: '#gate-abc',
        });
    });

    it('escapes </ so user-supplied text cannot close the script tag', () => {
        const out = buildJsonLd("evil-id\"></script><script>alert('xss')</script>");
        expect(out).not.toContain('</script>');
        expect(out).toContain('<\\/script>');
    });
});
