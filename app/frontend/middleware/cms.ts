// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Route-level guard for CMS admin pages (pages/admin/cms/**), used with 'admin':
 *   definePageMeta({ middleware: ['admin', 'cms'] })
 *
 * Returns 404 when NUXT_PUBLIC_CMS_ENABLED is not "true", matching the backend
 * which omits the CMS routes from the API.
 */
export default defineNuxtRouteMiddleware(() => {
    if (!isCmsEnabled()) {
        throw createError({ statusCode: 404, statusMessage: 'Not Found' });
    }
});
