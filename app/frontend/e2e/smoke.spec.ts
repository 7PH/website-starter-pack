// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { expect, test } from '@playwright/test';

test('app loads and backend is reachable', async ({ page }) => {
    // Frontend serves a page
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);

    // Backend healthcheck through Traefik
    const healthcheck = await page.request.get('/api/v1/healthcheck');
    expect(healthcheck.ok()).toBeTruthy();
    const body = await healthcheck.json();
    expect(body.status).toBe('ok');
    expect(body.database).toBe('ok');
});
