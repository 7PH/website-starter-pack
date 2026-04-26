// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

// Smoke coverage for the dynamic /robots.txt route and the auto-generated
// /sitemap.xml. Detailed schema/breadcrumb coverage lives in the sub-app
// where actual content pages exist.

import { expect, test } from '@playwright/test';

test('/robots.txt is dynamic and includes Sitemap line', async ({ request }) => {
    const response = await request.get('/robots.txt');
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('text/plain');

    const body = await response.text();
    expect(body).toMatch(/^User-agent:\s*\*/m);
    expect(body).toMatch(/Disallow:\s*\/admin/);
    expect(body).toMatch(/Disallow:\s*\/api/);
    expect(body).toMatch(/^Sitemap:\s*\S+\/sitemap\.xml/m);
});

test('/sitemap.xml returns valid XML with default URLs', async ({ request }) => {
    const response = await request.get('/sitemap.xml');
    expect(response.status()).toBe(200);

    const body = await response.text();
    expect(body).toContain('<?xml');
    expect(body).toContain('<urlset');
    // Default URLs shipped by the starterpack:
    expect(body).toContain('<loc>');
    expect(body).toMatch(/legal\/privacy/);
    expect(body).toMatch(/legal\/terms/);
    expect(body).toMatch(/legal\/cookies/);
});
