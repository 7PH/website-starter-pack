import type { Component } from 'vue';

/**
 * Async component loader type.
 * Returns a Promise that resolves to a module with a default export.
 */
export type AsyncComponentLoader = () => Promise<{ default: Component }>;

/**
 * Override core components with custom implementations.
 *
 * Keys must match the override key used in core components:
 * - 'OrganizationsCreateModal' - Custom organization creation modal
 * - 'OrganizationsPageActions' - Custom actions header on organizations list page
 * - 'OrganizationsSubscriptionModal' - Custom billing/subscription UI
 * - 'MessagesPageActions' - Custom actions header on messages list page
 * - 'ModalAuth' - Custom authentication flow
 *
 * Values must be async import functions for proper code splitting:
 *   () => import('~/components/custom/MyComponent.vue')
 *
 * Override components must match the original's props/events contract.
 *
 * @example
 * export const componentOverrides: Record<string, AsyncComponentLoader> = {
 *     'OrganizationsCreateModal': () => import('~/components/custom/OrgCreateModal.vue'),
 * };
 */
export const componentOverrides: Record<string, AsyncComponentLoader> = {
    // Add your component overrides here
};
