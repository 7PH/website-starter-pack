// ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

/**
 * Premium source constants - identifies where a user's premium access comes from.
 */
export const PREMIUM_SOURCE = {
    PERSONAL: 'personal',
    ORGANIZATION: 'organization',
    BOTH: 'both',
} as const;

export type PremiumSource = (typeof PREMIUM_SOURCE)[keyof typeof PREMIUM_SOURCE] | null;

/**
 * Composable for organization-related status and premium source tracking.
 * Extracts organization logic from components for better reusability.
 */
export function useOrganizationStatus() {
    const auth = useAuth();
    const config = useRuntimeConfig();

    // Check if organizations feature is enabled
    const organizationsEnabled = computed(() => String(config.public.organizationsEnabled) === 'true');

    // Premium source tracking
    const hasPersonalSubscription = computed(() => auth.user?.has_personal_subscription ?? false);

    // Organization context (only when feature enabled)
    const organizations = computed(() => (organizationsEnabled.value ? (auth.user?.organizations ?? []) : []));

    const orgsWithPremiumSeat = computed(() => organizations.value.filter((org) => org.has_premium_seat));

    const isOrgAdmin = computed(() => organizations.value.some((org) => org.is_admin));

    const adminOrgs = computed(() => organizations.value.filter((org) => org.is_admin));

    // Determine premium source(s) for display
    const premiumSource = computed<PremiumSource>(() => {
        const hasPersonal = hasPersonalSubscription.value;
        const hasOrgSeat = orgsWithPremiumSeat.value.length > 0;

        if (hasPersonal && hasOrgSeat) return PREMIUM_SOURCE.BOTH;
        if (hasPersonal) return PREMIUM_SOURCE.PERSONAL;
        if (hasOrgSeat) return PREMIUM_SOURCE.ORGANIZATION;
        return null;
    });

    // Get the primary org providing premium (first one with seat)
    const premiumOrg = computed(() => orgsWithPremiumSeat.value[0] ?? null);

    // First org user is admin of (for "Manage Organization" link)
    const firstAdminOrg = computed(() => adminOrgs.value[0] ?? null);

    // First org user is member of (for display)
    const firstOrg = computed(() => organizations.value[0] ?? null);

    // Check if user is admin of the org providing their premium seat
    const isAdminOfPremiumOrg = computed(() => {
        if (!premiumOrg.value) return false;
        return adminOrgs.value.some((o) => o.organization_id === premiumOrg.value?.organization_id);
    });

    return {
        // Feature flag
        organizationsEnabled,

        // Organization data
        organizations,
        orgsWithPremiumSeat,
        adminOrgs,
        firstOrg,
        firstAdminOrg,
        premiumOrg,

        // Status flags
        hasPersonalSubscription,
        isOrgAdmin,
        isAdminOfPremiumOrg,
        premiumSource,
    };
}
