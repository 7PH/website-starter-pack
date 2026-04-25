// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Account page tabs configuration.
 * Projects can extend by creating config/account-tabs-ext.ts with PROJECT_ACCOUNT_TABS.
 */

import { defineAsyncComponent, type Component } from 'vue';

export interface AccountTabItem {
    /** Unique tab identifier */
    id: string;
    /** i18n key for display label */
    label: string;
    /** Icon name (e.g., 'i-lucide-user') */
    icon?: string;
    /** Vue component to render for this tab */
    component: Component;
    /** Sort order (lower = left in tab bar) */
    order?: number;
    /** Optional condition function - tab hidden if returns false */
    condition?: () => boolean;
}

/**
 * Core account tabs.
 * These are managed by the starterpack.
 */
export const CORE_ACCOUNT_TABS: AccountTabItem[] = [
    {
        id: 'account',
        label: 'core.account.tabs.account',
        icon: 'i-lucide-user',
        component: defineAsyncComponent(() => import('~/components/account/AccountInfoTab.vue')),
        order: 10,
    },
    {
        id: 'password',
        label: 'core.account.tabs.password',
        icon: 'i-lucide-lock',
        component: defineAsyncComponent(() => import('~/components/account/PasswordTab.vue')),
        order: 20,
    },
    {
        id: 'organizations',
        label: 'core.account.tabs.organizations',
        icon: 'i-lucide-building-2',
        component: defineAsyncComponent(() => import('~/components/account/OrganizationsTab.vue')),
        order: 30,
        condition: () => {
            const config = useRuntimeConfig();
            return String(config.public.organizationsEnabled) === 'true';
        },
    },
    {
        id: 'billing',
        label: 'core.account.tabs.billing',
        icon: 'i-lucide-credit-card',
        component: defineAsyncComponent(() => import('~/components/account/BillingTab.vue')),
        order: 40,
        condition: () => {
            const config = useRuntimeConfig();
            return String(config.public.stripeEnabled) === 'true';
        },
    },
    {
        id: 'privacy',
        label: 'core.account.tabs.privacy',
        icon: 'i-lucide-shield',
        component: defineAsyncComponent(() => import('~/components/account/PrivacyTab.vue')),
        order: 50,
    },
];
