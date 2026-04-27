import type { Component } from 'vue';

/**
 * Override core components with custom implementations.
 *
 * Keys must match the override key used in core components:
 * - 'PageHeader' - Custom site header. Must mirror PageHeader's contract
 *     (no public props/events; consumes useAuth/useStripe/useAppLocale/etc.).
 * - 'PageFooter' - Custom site footer. No props/events.
 * - 'OrganizationsCreateModal' - Custom organization creation modal
 * - 'OrganizationsPageActions' - Custom actions header on organizations list page
 * - 'OrganizationsSubscriptionModal' - Custom billing/subscription UI
 * - 'MessagesPageActions' - Custom actions header on messages list page
 * - 'ModalAuth' - Custom authentication flow
 * - 'Breadcrumb' - Custom breadcrumb visual.
 *     IMPORTANT: your replacement MUST call `useBreadcrumb(items)` first thing
 *     in setup so BreadcrumbList JSON-LD stays emitted. Skipping it silently
 *     drops the page's structured data — Googlebot won't see the breadcrumb.
 *
 * Values are Vue components imported directly. For lazy-loaded overrides,
 * wrap with `defineAsyncComponent` from Vue.
 *
 * Override components must match the original's props/events contract.
 *
 * @example
 * ```ts
 * import { defineAsyncComponent } from 'vue';
 * import MyHeader from '~/components/custom/MyHeader.vue';
 *
 * export const componentOverrides: Record<string, Component> = {
 *     PageHeader: MyHeader,
 *     SomeBigModal: defineAsyncComponent(() => import('~/components/custom/Big.vue')),
 * };
 * ```
 */
export const componentOverrides: Record<string, Component> = {
    // Add your component overrides here
};
