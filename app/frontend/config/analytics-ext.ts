/**
 * Analytics for this app: any provider (Plausible, Umami, Rybbit, Matomo, GA...), hosted or self-hosted elsewhere.
 * Empty `scripts` = no analytics. Read at build time, so rebuild the frontend after changing it.
 * Add a link to the provider's dashboard via PROJECT_ADMIN_NAV in admin-nav-ext.ts (`href` + `external: true`).
 *
 * @example Plausible
 * export const ANALYTICS: AnalyticsConfig = {
 *     scripts: [{ src: 'https://plausible.io/js/pa-XXXX.js', defer: true }],
 *     origins: ['https://plausible.io'],
 *     track: (name, data) => window.plausible?.(name, { props: data }),
 * };
 *
 * @example Umami
 * scripts: [{ src: 'https://cloud.umami.is/script.js', defer: true, 'data-website-id': '<id>' }],
 * origins: ['https://cloud.umami.is', 'https://api-gateway.umami.dev'],
 * track: (name, data) => window.umami?.track(name, data),
 *
 * Declare the provider's global for TypeScript, eg `declare global { interface Window { plausible?: ... } }`.
 */

import type { AnalyticsConfig } from '../types/analytics';

export const ANALYTICS: AnalyticsConfig = {
    scripts: [],
    origins: [],
    track: () => {},
};
