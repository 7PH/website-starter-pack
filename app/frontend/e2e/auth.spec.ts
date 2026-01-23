// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

import { expect, test } from '@playwright/test';

const testEmail = `test-${Date.now()}@example.com`;
const testPassword = 'TestPass123!';
const testFirstName = 'Test';
const testLastName = 'User';

test('auth flow: signup, logout, login', async ({ page }) => {
    // Signup
    await page.goto('/login?mode=signup');
    await page.waitForLoadState('networkidle');
    await page.getByPlaceholder('First name').fill(testFirstName);
    await page.getByPlaceholder('Last name').fill(testLastName);
    await page.getByPlaceholder('Email').fill(testEmail);
    await page.locator('input[autocomplete="new-password"]').first().fill(testPassword);
    await page.getByPlaceholder('Confirm password').fill(testPassword);
    await page.getByRole('button', { name: /create account/i }).click();
    await page.waitForURL('/');
    await expect(page.locator('header').getByText(testFirstName)).toBeVisible();

    // Protected route accessible when logged in
    await page.goto('/account');
    await expect(page).toHaveURL('/account');

    // Logout redirects to home - open user dropdown and click logout
    await page.getByRole('button', { name: testFirstName }).click();
    await page.getByRole('menuitem', { name: /log out/i }).click();
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('link', { name: /log in/i })).toBeVisible();

    // Protected route redirects to login when logged out
    await page.goto('/account');
    await expect(page).toHaveURL(/\/login\?redirect=/);

    // Login with redirect back to account
    await page.waitForLoadState('networkidle');
    await page.getByPlaceholder('Email').fill(testEmail);
    await page.locator('input[autocomplete="current-password"]').fill(testPassword);
    await page.getByRole('button', { name: /^log in$/i }).click();
    await expect(page).toHaveURL('/account');
    await expect(page.locator('header').getByText(testFirstName)).toBeVisible();
});
