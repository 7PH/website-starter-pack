// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Route-level guard for the managed-accounts feature. Applied to:
 *   - pages/managed-account-groups/*
 *   - pages/c/[token].vue (the public picker)
 *
 * Returns 404 when NUXT_PUBLIC_MANAGED_ACCOUNTS_ENABLED is not "true",
 * matching the backend which omits the corresponding routes from the API.
 */
export default defineNuxtRouteMiddleware(() => {
    const config = useRuntimeConfig();
    if (String(config.public.managedAccountsEnabled) !== 'true') {
        throw createError({ statusCode: 404, statusMessage: 'Not Found' });
    }
});
