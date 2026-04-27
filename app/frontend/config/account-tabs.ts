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
        // Managed accounts can't edit their own name/email (owner manages those).
        condition: () => useAuth().user?.auth_method !== 'access_code',
    },
    {
        id: 'password',
        label: 'core.account.tabs.password',
        icon: 'i-lucide-lock',
        component: defineAsyncComponent(() => import('~/components/account/PasswordTab.vue')),
        order: 20,
        // Managed accounts have no password.
        condition: () => useAuth().user?.auth_method !== 'access_code',
    },
    {
        id: 'organizations',
        label: 'core.account.tabs.organizations',
        icon: 'i-lucide-building-2',
        component: defineAsyncComponent(() => import('~/components/account/OrganizationsTab.vue')),
        order: 30,
        condition: () => {
            const config = useRuntimeConfig();
            const auth = useAuth();
            return String(config.public.organizationsEnabled) === 'true' && auth.user?.auth_method !== 'access_code';
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
            const auth = useAuth();
            return String(config.public.stripeEnabled) === 'true' && auth.user?.auth_method !== 'access_code';
        },
    },
    {
        id: 'privacy',
        label: 'core.account.tabs.privacy',
        icon: 'i-lucide-shield',
        component: defineAsyncComponent(() => import('~/components/account/PrivacyTab.vue')),
        order: 50,
        // Privacy tab hosts the self-delete flow, which the backend blocks for
        // managed accounts. Hide it so the kid never sees a button that 403s.
        condition: () => useAuth().user?.auth_method !== 'access_code',
    },
];
