/**
 * Premium that comes from outside this app's Stripe checkout: an invoice deal, a purchase order paid by an
 * institution, a partner that pays for its people, an order still waiting for its payment…
 *
 * Return null (the default) and nothing changes. Return an ExternalPremium and the core billing UI says so instead of
 * selling a Stripe subscription, so nobody pays twice:
 * - useUserExternalPremium: the header shows `label` in place of "Upgrade" (when the user isn't premium yet), and the
 *   account billing tab shows the notice and hides "Subscribe personally".
 * - useOrganizationExternalPremium: the organization's billing tab shows the notice in place of the Stripe buttons,
 *   and the admin billing tab shows it above the balance.
 *
 * Both run inside a component setup, so they can read stores and fetch (keep it cheap: the header calls the first one
 * on every page).
 *
 * @example
 * export function useUserExternalPremium(): ComputedRef<ExternalPremium | null> {
 *     const auth = useAuth();
 *     return computed(() =>
 *         auth.user?.custom_data?.invoice_pending
 *             ? { label: 'Premium on its way', description: 'Your company is paying by invoice.', to: '/team' }
 *             : null,
 *     );
 * }
 */

import type { ComputedRef, Ref } from 'vue';

export interface ExternalPremium {
    /** A few words: shown in the header (icon only on phones) and as the billing source. */
    label: string;
    /** One or two sentences on the billing tabs. */
    description?: string;
    /** Where it is managed; the header and the notice link there. */
    to?: string;
}

export function useUserExternalPremium(): ComputedRef<ExternalPremium | null> {
    return computed(() => null);
}

export function useOrganizationExternalPremium(_orgId: Ref<number>): ComputedRef<ExternalPremium | null> {
    return computed(() => null);
}
